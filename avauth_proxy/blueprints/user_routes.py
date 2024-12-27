# avauth_proxy/blueprints/user_routes.py

from flask import Blueprint, render_template, request, jsonify, abort
from flask import current_app, session as flask_session
from sqlalchemy.orm import Session
from avauth_proxy.models import User, Proxy
from avauth_proxy.services.user_manager import UserManager
from avauth_proxy.utils.decorator_utils import log_route_error, admin_required

user_bp = Blueprint('users', __name__)

def get_user_manager():
    """
    Creates a UserManager instance with a new database session.

    This helper ensures we have a fresh database session for each request
    and properly closes it afterward.

    Returns:
        tuple: (UserManager instance, database session)
    """
    db_session = Session()
    return UserManager(db_session), db_session

@user_bp.route('/users')
@admin_required
@log_route_error()
def list_users():
    """
    Display the user management interface.

    This page shows all users in the system and allows administrators to:
    - Add new users
    - Modify user roles
    - Manage proxy access permissions
    - Deactivate users

    Returns:
        str: Rendered user management template
    """
    manager, session = get_user_manager()
    try:
        # Get all users and their proxy associations
        users = session.query(User).all()
        proxies = session.query(Proxy).all()

        # For each user, get their proxy access information
        user_data = []
        for user in users:
            proxy_access = manager.get_user_proxies(user.id)
            user_data.append({
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'proxies': proxy_access
            })

        return render_template(
            'users/manage.html',
            users=user_data,
            proxies=proxies,
            current_user=flask_session.get('user')
        )
    finally:
        session.close()

@user_bp.route('/users', methods=['POST'])
@admin_required
@log_route_error()
def create_user():
    """
    Create a new user account.

    Expected JSON payload:
    {
        "email": "user@example.com",
        "role": "user",  # Optional, defaults to "user"
        "proxy_access": [  # Optional
            {
                "proxy_id": 1,
                "access_level": "read"
            }
        ]
    }

    Returns:
        JSON response with created user information
    """
    manager, session = get_user_manager()
    try:
        data = request.get_json()

        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400

        try:
            # Create the user
            user = manager.create_user(
                email=data['email'],
                role=data.get('role', 'user')
            )

            # If proxy access was specified, grant it
            if 'proxy_access' in data:
                for access in data['proxy_access']:
                    manager.grant_proxy_access(
                        user.id,
                        access['proxy_id'],
                        access.get('access_level', 'read')
                    )

            return jsonify({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat()
                }
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

    finally:
        session.close()

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@log_route_error()
def update_user(user_id):
    """
    Update a user's information or access permissions.

    Expected JSON payload:
    {
        "role": "admin",  # Optional
        "is_active": true,  # Optional
        "proxy_access": [  # Optional
            {
                "proxy_id": 1,
                "access_level": "write"
            }
        ]
    }

    Returns:
        JSON response with updated user information
    """
    manager, session = get_user_manager()
    try:
        data = request.get_json()
        user = session.query(User).get(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        try:
            # Update role if specified
            if 'role' in data:
                user = manager.update_user_role(user_id, data['role'])

            # Update active status if specified
            if 'is_active' in data:
                if data['is_active']:
                    user.is_active = True
                else:
                    manager.deactivate_user(user_id)

            # Update proxy access if specified
            if 'proxy_access' in data:
                # First, get current access
                current_access = manager.get_user_proxies(user_id)
                current_proxy_ids = {p['proxy_id'] for p in current_access}

                # Determine access to add/update/remove
                new_proxy_ids = {p['proxy_id'] for p in data['proxy_access']}

                # Remove access that's no longer in the list
                for proxy_id in current_proxy_ids - new_proxy_ids:
                    manager.revoke_proxy_access(user_id, proxy_id)

                # Add/update remaining access
                for access in data['proxy_access']:
                    manager.grant_proxy_access(
                        user_id,
                        access['proxy_id'],
                        access.get('access_level', 'read')
                    )

            return jsonify({
                'message': 'User updated successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'proxies': manager.get_user_proxies(user_id)
                }
            })

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to update user: {str(e)}'}), 500

    finally:
        session.close()

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@log_route_error()
def delete_user(user_id):
    """
    Delete a user account.

    This will remove all proxy access associations for the user.

    Returns:
        JSON response indicating success
    """
    manager, session = get_user_manager()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get proxy access for logging
        proxy_access = manager.get_user_proxies(user_id)

        try:
            # Remove all proxy access
            for access in proxy_access:
                manager.revoke_proxy_access(user_id, access['proxy_id'])

            # Delete the user
            session.delete(user)
            session.commit()

            return jsonify({
                'message': 'User and all associated access permissions deleted'
            })

        except Exception as e:
            session.rollback()
            return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500

    finally:
        session.close()

@user_bp.route('/users/<int:user_id>/proxies')
@admin_required
@log_route_error()
def get_user_proxy_access(user_id):
    """
    Get all proxy access permissions for a user.

    Returns:
        JSON response with user's proxy access information
    """
    manager, session = get_user_manager()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        proxy_access = manager.get_user_proxies(user_id)
        return jsonify(proxy_access)

    finally:
        session.close()

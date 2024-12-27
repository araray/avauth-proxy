from functools import wraps
from flask import session, redirect, url_for, current_app, abort
from avauth_proxy.utils.logging_utils import log_event

def is_admin():
    """
    Check if the current user has admin privileges.

    This function looks at both the user's role in the session
    and verifies their email against the configured admin list.

    Returns:
        bool: True if user is an admin, False otherwise
    """
    if 'user' not in session:
        return False

    user_info = session['user']
    user_email = user_info.get('email')

    # Check against configured admin emails
    admin_emails = current_app.config.get('ADMIN_EMAILS', [])

    # Also check if user has admin role in session
    user_role = user_info.get('role')

    return user_email in admin_emails or user_role == 'admin'

def admin_required(f):
    """
    Decorator to restrict routes to admin users only.

    This decorator:
    1. Verifies user is logged in
    2. Checks admin privileges
    3. Logs unauthorized access attempts
    4. Redirects or returns 403 as appropriate

    Usage:
        @app.route('/admin/dashboard')
        @admin_required
        def admin_dashboard():
            return render_template('admin/dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Not logged in - redirect to login
            log_event(
                "Unauthorized access attempt to admin route (not logged in)",
                "auth_error"
            )
            return redirect(url_for('auth.login'))

        if not is_admin():
            # Logged in but not admin - forbidden
            user_email = session['user'].get('email', 'unknown')
            log_event(
                f"Unauthorized access attempt to admin route by {user_email}",
                "auth_error"
            )
            return abort(403)

        return f(*args, **kwargs)
    return decorated_function

def require_proxy_access(access_level='read'):
    """
    Decorator to restrict routes based on proxy access permissions.

    This decorator:
    1. Verifies user is logged in
    2. Checks user has required access level for the proxy
    3. Logs unauthorized access attempts

    Args:
        access_level: Minimum required access level ('read', 'write', 'admin')

    Usage:
        @app.route('/proxy/<int:proxy_id>/configure')
        @require_proxy_access('write')
        def configure_proxy(proxy_id):
            return render_template('proxy/configure.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                log_event(
                    "Unauthorized proxy access attempt (not logged in)",
                    "auth_error"
                )
                return redirect(url_for('auth.login'))

            # Get proxy_id from route parameters
            proxy_id = kwargs.get('proxy_id')
            if not proxy_id:
                # If no proxy_id in route, check function arguments
                proxy_id = next(
                    (arg for arg in args if isinstance(arg, int)),
                    None
                )

            if not proxy_id:
                log_event(
                    "Proxy access check failed - no proxy_id found",
                    "auth_error"
                )
                return abort(400)

            user_email = session['user'].get('email')

            # Always allow admin users
            if is_admin():
                return f(*args, **kwargs)

            # Check user's access level for this proxy
            from avauth_proxy.services.user_manager import UserManager
            manager, db_session = get_user_manager()
            try:
                user = manager.get_user_by_email(user_email)
                if not user:
                    log_event(
                        f"User not found in database: {user_email}",
                        "auth_error"
                    )
                    return abort(403)

                proxy_access = manager.get_user_proxies(user.id)
                proxy_permission = next(
                    (p for p in proxy_access if p['proxy_id'] == proxy_id),
                    None
                )

                if not proxy_permission:
                    log_event(
                        f"User {user_email} attempted to access unauthorized proxy {proxy_id}",
                        "auth_error"
                    )
                    return abort(403)

                # Check access level
                access_levels = {
                    'read': 0,
                    'write': 1,
                    'admin': 2
                }

                required_level = access_levels.get(access_level, 0)
                user_level = access_levels.get(proxy_permission['access_level'], 0)

                if user_level < required_level:
                    log_event(
                        f"User {user_email} has insufficient permissions for proxy {proxy_id} "
                        f"(required: {access_level}, has: {proxy_permission['access_level']})",
                        "auth_error"
                    )
                    return abort(403)

                return f(*args, **kwargs)

            finally:
                db_session.close()

        return decorated_function
    return decorator

def get_user_manager():
    """
    Create a UserManager instance with a new database session.

    This helper ensures we have a fresh database session for each request.

    Returns:
        tuple: (UserManager instance, database session)
    """
    from sqlalchemy.orm import Session
    db_session = Session()
    from avauth_proxy.services.user_manager import UserManager
    return UserManager(db_session), db_session

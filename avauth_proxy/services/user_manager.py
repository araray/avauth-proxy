# avauth_proxy/services/user_manager.py

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Session
from avauth_proxy.models import User, UserProxy, Proxy
from avauth_proxy.utils.logging_utils import log_event

class UserManager:
    """
    Manages user operations and access control for the proxy system.

    This service handles:
    - User creation and management
    - User-proxy access control
    - Authentication verification
    - Session management
    """

    def __init__(self, session: Session):
        """
        Initialize the user manager.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def create_user(self, email: str, role: str = 'user') -> User:
        """
        Create a new user in the system.

        Args:
            email: User's email address (must be unique)
            role: User's role (default: 'user')

        Returns:
            Created User instance

        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing = self.session.query(User).filter_by(email=email).first()
        if existing:
            raise ValueError(f"User with email {email} already exists")

        user = User(
            email=email,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )

        try:
            self.session.add(user)
            self.session.commit()
            log_event(f"Created user: {email}", "user_created")
            return user
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to create user: {str(e)}")

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            User instance if found, None otherwise
        """
        return self.session.query(User).filter_by(email=email).first()

    def update_user_role(self, user_id: int, new_role: str) -> User:
        """
        Update a user's role.

        Args:
            user_id: ID of the user to update
            new_role: New role to assign

        Returns:
            Updated User instance

        Raises:
            ValueError: If user not found
        """
        user = self.session.query(User).get(user_id)
        if not user:
            raise ValueError(f"User ID {user_id} not found")

        old_role = user.role
        user.role = new_role

        try:
            self.session.commit()
            log_event(
                f"Updated user {user.email} role from {old_role} to {new_role}",
                "user_role_updated"
            )
            return user
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to update user role: {str(e)}")

    def deactivate_user(self, user_id: int):
        """
        Deactivate a user account.

        Args:
            user_id: ID of the user to deactivate

        Raises:
            ValueError: If user not found
        """
        user = self.session.query(User).get(user_id)
        if not user:
            raise ValueError(f"User ID {user_id} not found")

        user.is_active = False

        try:
            self.session.commit()
            log_event(f"Deactivated user: {user.email}", "user_deactivated")
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to deactivate user: {str(e)}")

    def grant_proxy_access(
        self,
        user_id: int,
        proxy_id: int,
        access_level: str = 'read'
    ) -> UserProxy:
        """
        Grant a user access to a proxy service.

        Args:
            user_id: ID of the user
            proxy_id: ID of the proxy service
            access_level: Access level to grant (read/write/admin)

        Returns:
            Created UserProxy association

        Raises:
            ValueError: If user or proxy not found
        """
        user = self.session.query(User).get(user_id)
        proxy = self.session.query(Proxy).get(proxy_id)

        if not user:
            raise ValueError(f"User ID {user_id} not found")
        if not proxy:
            raise ValueError(f"Proxy ID {proxy_id} not found")

        # Check if association already exists
        existing = self.session.query(UserProxy).filter(
            and_(
                UserProxy.user_id == user_id,
                UserProxy.proxy_id == proxy_id
            )
        ).first()

        if existing:
            existing.access_level = access_level
            try:
                self.session.commit()
                log_event(
                    f"Updated access for user {user.email} to proxy {proxy.service_name}",
                    "proxy_access_updated"
                )
                return existing
            except Exception as e:
                self.session.rollback()
                raise RuntimeError(f"Failed to update proxy access: {str(e)}")

        association = UserProxy(
            user_id=user_id,
            proxy_id=proxy_id,
            access_level=access_level,
            created_at=datetime.utcnow()
        )

        try:
            self.session.add(association)
            self.session.commit()
            log_event(
                f"Granted {access_level} access to user {user.email} "
                f"for proxy {proxy.service_name}",
                "proxy_access_granted"
            )
            return association
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to grant proxy access: {str(e)}")

    def revoke_proxy_access(self, user_id: int, proxy_id: int):
        """
        Revoke a user's access to a proxy service.

        Args:
            user_id: ID of the user
            proxy_id: ID of the proxy service

        Raises:
            ValueError: If association not found
        """
        association = self.session.query(UserProxy).filter(
            and_(
                UserProxy.user_id == user_id,
                UserProxy.proxy_id == proxy_id
            )
        ).first()

        if not association:
            raise ValueError(
                f"No access found for user {user_id} to proxy {proxy_id}"
            )

        try:
            self.session.delete(association)
            self.session.commit()
            log_event(
                f"Revoked access for user {association.user.email} "
                f"to proxy {association.proxy.service_name}",
                "proxy_access_revoked"
            )
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Failed to revoke proxy access: {str(e)}")

    def get_user_proxies(self, user_id: int) -> List[Dict]:
        """
        Get all proxies accessible to a user.

        Args:
            user_id: ID of the user

        Returns:
            List of dictionaries containing proxy information and access levels
        """
        associations = self.session.query(UserProxy).filter_by(
            user_id=user_id
        ).all()

        return [
            {
                'proxy_id': assoc.proxy_id,
                'service_name': assoc.proxy.service_name,
                'access_level': assoc.access_level,
                'granted_at': assoc.created_at
            }
            for assoc in associations
        ]

    def get_proxy_users(self, proxy_id: int) -> List[Dict]:
        """
        Get all users with access to a proxy service.

        Args:
            proxy_id: ID of the proxy service

        Returns:
            List of dictionaries containing user information and access levels
        """
        associations = self.session.query(UserProxy).filter_by(
            proxy_id=proxy_id
        ).all()

        return [
            {
                'user_id': assoc.user_id,
                'email': assoc.user.email,
                'access_level': assoc.access_level,
                'granted_at': assoc.created_at
            }
            for assoc in associations
        ]

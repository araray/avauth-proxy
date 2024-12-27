from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Template(Base):
    """Nginx configuration template model."""
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    proxies = relationship('UserProxy', back_populates='user')

    def can_access_proxy(self, proxy_id):
        """Check if user has access to a specific proxy."""
        return any(up.proxy_id == proxy_id for up in self.proxies)

class Proxy(Base):
    """Proxy configuration and health status model."""
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    service_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    template_id = Column(Integer, ForeignKey('templates.id'))
    auth_required = Column(Boolean, default=False)
    custom_directives = Column(Text)
    allowed_emails = Column(Text)  # JSON list of emails
    allowed_domains = Column(Text)  # JSON list of domains
    health_status = Column(String, default='unknown')  # ok, warning, error, deactivated, stopped
    health_check_endpoint = Column(String, default='/health')
    expected_status = Column(Integer, default=200)
    expected_response = Column(JSON)  # Expected JSON response structure
    last_checked = Column(DateTime)
    metrics = relationship('ProxyMetrics', back_populates='proxy')
    template = relationship('Template')

class ProxyMetrics(Base):
    """Metrics collection for proxy monitoring."""
    __tablename__ = 'proxy_metrics'

    id = Column(Integer, primary_key=True)
    proxy_id = Column(Integer, ForeignKey('proxies.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    incoming_requests = Column(Integer, default=0)
    outgoing_requests = Column(Integer, default=0)
    incoming_bytes = Column(Integer, default=0)
    outgoing_bytes = Column(Integer, default=0)
    response_time_ms = Column(Integer)  # Average response time
    error_count = Column(Integer, default=0)

    proxy = relationship('Proxy', back_populates='metrics')

class UserProxy(Base):
    """Many-to-many relationship between users and proxies."""
    __tablename__ = 'user_proxies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    proxy_id = Column(Integer, ForeignKey('proxies.id'), nullable=False)
    access_level = Column(String, default='read')  # read, write, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='proxies')
    proxy = relationship('Proxy')

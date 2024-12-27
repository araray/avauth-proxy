from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default='user')
    proxies = relationship('UserProxy', back_populates='user')

class UserProxy(Base):
    __tablename__ = 'user_proxies'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    proxy_id = Column(Integer, ForeignKey('proxies.id'), nullable=False)
    user = relationship('User', back_populates='proxies')

class Proxy(Base):
    __tablename__ = 'proxies'
    id = Column(Integer, primary_key=True)
    service_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    template = Column(String, nullable=False)
    auth_required = Column(Boolean, default=False)
    custom_directives = Column(Text)
    allowed_emails = Column(Text)
    allowed_domains = Column(Text)
    health_status = Column(String, default='unknown')  # 'ok', 'warning', 'error'
    last_checked = Column(DateTime, default=datetime.utcnow)

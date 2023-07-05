import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from werkzeug.security import generate_password_hash

Base = declarative_base()


class BaseMixin:
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, BaseMixin):
    __tablename__ = 'users'
    # __table_args__ = {'extend_existing': True}

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hash_password = Column(String(255), nullable=False)
    verified = Column(Boolean, nullable=False, server_default='False')
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))

    # role_id: UUID = UUID('499be5e3-cceb-4e18-8dd6-4fbfaaa907b4')
    # verified
    def __init__(
            self,
            first_name: str,
            last_name: str,
            email: str,
            password: str
    ) -> None:

        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.hash_password = generate_password_hash(password)

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class Role(Base, BaseMixin):
    __tablename__ = 'roles'
    # __table_args__ = {'extend_existing': True}

    name = Column(String(15), nullable=False)
    description = Column(String(255), nullable=False)

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f'<User {self.name}>'


class AccountHistory(Base, BaseMixin):
    __tablename__ = 'account_history'
    # __table_args__ = {'extend_existing': True}

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user_agent = Column(String(50), nullable=False, server_default='default UA')  # здесь потом должна быть функция получающая useragent


class RefreshToken(Base, BaseMixin):
    __tablename__ = 'refresh_tokens'
    # __table_args__ = {'extend_existing': True}

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user_token = Column(String(255), nullable=False, server_default='default UT')  # здесь потом должна быть функция получающая user_token
    is_active = Column(Boolean, nullable=False, server_default='False')


# op.execute(r"INSERT INTO roles (name, description) VALUES ('admin', 'admin')")

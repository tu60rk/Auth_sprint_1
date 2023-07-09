import re

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, validator, constr, Field
from sqlalchemy import MetaData


def validate_password(value):
    password_length = len(value)
    if password_length < 8:
        raise ValueError('The password must be at least 8 characters long')
    if not re.search('[A-Z]', value):
        raise ValueError('The password must contain at least one uppercase letter')
    if not re.search('[a-z]', value):
        raise ValueError('The password must contain at least one lowercase letter')
    if not re.search('[0-9]', value):
        raise ValueError('The password must contain at least one digit')
    return value

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @validator('password')
    @classmethod
    def validate_password(cls, value):
        return validate_password(value)

    @validator('first_name')
    @classmethod
    def first_name_contains_only_letters(cls, value):
        if not value.isalpha():
            raise ValueError('The first name must contain only alphabethical symbols')
        return value

    @validator('last_name')
    @classmethod
    def last_name_contains_only_letters(cls, value):
        if not value.isalpha():
            raise ValueError('The last name must contain only alphabethical symbols')
        return value
    
    class Config:
        orm_mode = True


class UserInDB(BaseModel):
    id: UUID
    email: str
    role_id: UUID

    class Config:
        orm_mode = True

class LoginUserSchema(BaseModel):
    email: EmailStr
    password: str
    set_cookie: bool = False

    @validator('password')
    @classmethod
    def validate_password(cls, value):
        return validate_password(value)
    
    class Config:
        orm_mode = True


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    repeat_password: str

    @validator('new_password')
    @classmethod
    def validate_password(cls, value):
        return validate_password(value)

class LoginHistory(BaseModel):
    user_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LoginHistoryCreate(BaseModel):
    user_agent: str


import re

from uuid import UUID

from pydantic import BaseModel, EmailStr, validator, constr



class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @validator('password')
    @classmethod
    def validate_password(cls, value):
        password_length = len(value)
        if password_length < 8: #or password_length > 24:
            raise ValueError('The password must be between 8 long')
        if not re.search('[A-Z]', value):
            raise ValueError('The password must be have one upper letter')
        if not re.search('[a-z]', value):
            raise ValueError('The password must be have one lower letter')
        if not re.search('[0-9]', value):
            raise ValueError('The password must be have one digit')
        return value

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
    password: str
    role_id: int

    class Config:
        orm_mode = True

class LoginUserSchema(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    @classmethod
    def validate_password(cls, value):
        password_length = len(value)
        if password_length < 8: #or password_length > 24:
            raise ValueError('The password must be between 8 long')
        if not re.search('[A-Z]', value):
            raise ValueError('The password must be have one upper letter')
        if not re.search('[a-z]', value):
            raise ValueError('The password must be have one lower letter')
        if not re.search('[0-9]', value):
            raise ValueError('The password must be have one digit')
        return value
    
    class Config:
        orm_mode = True
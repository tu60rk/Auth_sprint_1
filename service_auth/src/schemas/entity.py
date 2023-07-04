from uuid import UUID

from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

    @validator('password')
    @classmethod
    def validate_password(cls, value):
        password_length = len(value)
        if password_length < 8 or password_length > 24:
            raise ValueError('The password must be between 8 and 24 characters long')
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


class UserInDB(BaseModel):
    id: UUID
    first_name: str
    last_name: str

    class Config:
        orm_mode = True

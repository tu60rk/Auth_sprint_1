from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserInDB(BaseModel):
    id: UUID
    email: str
    password: str

    class Config:
        orm_mode = True


class ForgotPassword(BaseModel):
    email: EmailStr

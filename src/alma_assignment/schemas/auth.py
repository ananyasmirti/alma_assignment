import uuid

from pydantic import BaseModel, EmailStr


class AttorneyRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class AttorneyLogin(BaseModel):
    email: EmailStr
    password: str


class AttorneyResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

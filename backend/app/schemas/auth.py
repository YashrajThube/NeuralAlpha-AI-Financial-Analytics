from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default='user', pattern='^(admin|user)$')


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenData(BaseModel):
    access_token: str
    token_type: str = 'bearer'

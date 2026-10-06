from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    password: str
    name: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    name: str | None = None

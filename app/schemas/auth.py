from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class RegistrationResponse(BaseModel):
    message: str
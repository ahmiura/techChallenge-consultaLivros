from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    email: str | None = None
    is_active: bool | None = True
    is_superuser: bool | None = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str
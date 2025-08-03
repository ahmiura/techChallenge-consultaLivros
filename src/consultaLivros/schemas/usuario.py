from pydantic import BaseModel

class Usuario(BaseModel):
    username: str
    password: str

class UsuarioResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True 
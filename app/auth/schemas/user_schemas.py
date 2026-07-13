from pydantic import BaseModel


class BaseUserSchema(BaseModel):
    username: str
    password: str


class RegisterUserSchema(BaseUserSchema):
    pass


class LoginUserSchema(BaseUserSchema):
    pass

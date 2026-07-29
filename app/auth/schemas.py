from pydantic import BaseModel


class BaseUserSchema(BaseModel):
    username: str
    password: str


class RegisterUserSchema(BaseUserSchema):
    pass


class LoginUserSchema(BaseUserSchema):
    pass


class DeleteUserSchema(BaseModel):
    username: str


class CreateUserSchema(BaseUserSchema):
    database_url: str

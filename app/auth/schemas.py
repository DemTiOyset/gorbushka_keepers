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


class CreateUserSchema(BaseModel):
    username: str
    hashed_password: str
    database_url: str

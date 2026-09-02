from pydantic import BaseModel, ConfigDict


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


class ResponseUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str

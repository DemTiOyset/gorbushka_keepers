class BaseError(Exception):
    pass


class UserNotFoundError(BaseException):
    pass


class UserUnauthorizedError(BaseException):
    pass


class UserAlreadyExistError(BaseException):
    pass


class FailedInitialiseDatabaseError(BaseException):
    def __init__(self, detail: str):
        self.detail = detail

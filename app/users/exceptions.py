class BaseError(Exception):
    pass


class StoreAlreadyExistError(BaseError):
    pass


class TelegramDataAlreadyExist(BaseError):
    pass

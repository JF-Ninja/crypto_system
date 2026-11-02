class AuthError(Exception):
    pass

class TokenInvalidError(AuthError):
    pass

class TokenTypeMismatchError(AuthError):
    pass

class TokenNotFoundError(AuthError):
    pass

class UserDeactivatedError(AuthError):
    pass


class UserError(Exception):
    pass

class InvalidCredentialsError(UserError):
    pass

class EmptyUpdateFieldsError(UserError):
    pass

class UserNotFoundError(UserError):
    pass
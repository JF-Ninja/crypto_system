class MainError(Exception):
    pass

class AlertExistError(MainError):
    pass

class AssetCurrentPriceError(MainError):
    pass

class AssetNotFound(MainError):
    pass

class AuthError(Exception):
    pass

class TokenInvalidError(AuthError):
    pass

class ExternalServiceUnavailableError(Exception):
    pass
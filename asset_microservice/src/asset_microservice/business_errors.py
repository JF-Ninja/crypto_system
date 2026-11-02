class AssetError(Exception):
    pass

class AssetExistsError(AssetError):
    pass

class AssetNotFoundError(AssetError):
    pass

class ExternalServiceUnavailableError(Exception):
    pass
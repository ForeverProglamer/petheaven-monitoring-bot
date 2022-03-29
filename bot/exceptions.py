class DataAlreadyExistsInDBError(Exception):
    """Exception that is raised when trying to save data that already exists within data storage."""
    pass


class CantSaveToDBError(Exception):
    """Exception that is raised when saving data to storage fails."""
    pass


class DataNotFoundError(Exception):
    """Exception that is raised when no data found in data storage."""
    pass


class ServiceOperationFailedError(Exception):
    """Exception that is raised when service operation is failed to execute successfully."""
    pass

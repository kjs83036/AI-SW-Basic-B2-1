class BudgetAppError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


class ValidationError(BudgetAppError):
    pass


class NotFoundError(BudgetAppError):
    pass


class CategoryInUseError(BudgetAppError):
    pass


class StorageError(BudgetAppError):
    pass

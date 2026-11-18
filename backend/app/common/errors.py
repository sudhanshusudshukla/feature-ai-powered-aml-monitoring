"""Domain exceptions for error handling."""


class DomainError(Exception):
    """Base domain exception."""
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail or message
        super().__init__(self.message)


class DomainValidationError(DomainError):
    """Domain-specific validation error (HTTP 400)."""
    pass


class NotFoundError(DomainError):
    """Entity not found error (HTTP 404)."""
    pass


class AuthenticationError(DomainError):
    """Authentication failure error (HTTP 401)."""
    pass


class AuthorizationError(DomainError):
    """Authorization/permission error (HTTP 403)."""
    pass


class InvalidStateTransitionError(DomainError):
    """Invalid case state transition (HTTP 409)."""
    pass


class OptimisticLockConflictError(DomainError):
    """Optimistic locking conflict (HTTP 409)."""
    pass


class RuleEvaluationFailureError(DomainError):
    """Rule evaluation failure (HTTP 500/422 mapping)."""
    pass

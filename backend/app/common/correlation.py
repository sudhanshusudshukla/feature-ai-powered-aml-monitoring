"""Correlation ID utilities for request tracing."""
import uuid
from contextvars import ContextVar

# Context variable to store correlation ID for the current request
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for the current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get correlation ID from current context."""
    cid = correlation_id_var.get()
    if not cid:
        cid = generate_correlation_id()
        set_correlation_id(cid)
    return cid

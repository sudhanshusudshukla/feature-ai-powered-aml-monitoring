"""Structured logging configuration with correlation ID support."""
import logging
import sys
from app.common.correlation import get_correlation_id


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


def configure_logging():
    """Configure application logging with correlation support."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
        )
    )
    handler.addFilter(CorrelationFilter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

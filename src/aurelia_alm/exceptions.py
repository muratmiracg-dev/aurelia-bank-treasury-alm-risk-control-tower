"""Domain-specific exceptions."""


class AureliaALMError(Exception):
    """Base exception for the project."""


class ConfigurationError(AureliaALMError):
    """Raised when governed configuration is missing or invalid."""


class DataQualityError(AureliaALMError):
    """Raised when an input violates a critical data contract."""

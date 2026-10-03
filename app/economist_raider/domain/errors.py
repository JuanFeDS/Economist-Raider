"""Domain error hierarchy."""


class DomainError(Exception):
    """Base domain error."""


class DuplicateMeasurementError(DomainError):
    """Raised when a measurement for the same indicator+date already exists."""


class SourceNotFoundError(DomainError):
    """Raised when a requested source does not exist."""


class ValidationError(DomainError):
    """Raised when an entity fails business validation."""


class QuarantineError(DomainError):
    """Raised when a quarantined record is accessed unexpectedly."""

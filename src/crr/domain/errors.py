"""Domain validation errors shared by application boundaries."""


class DomainError(ValueError):
    """A deterministic domain validation failure."""

    code = "DOMAIN_VALIDATION_FAILED"


class StaleVersionError(DomainError):
    """A mutation was based on an obsolete aggregate version."""

    code = "STALE_VERSION"


class TenantBoundaryError(DomainError):
    """An operation crossed an organization boundary without authorization."""

    code = "TENANT_BOUNDARY_VIOLATION"

"""
Domain and Infrastructure Exceptions for PharmaTrace Nexus.
"""

class PharmaTraceError(Exception):
    """Base exception for all PharmaTrace errors."""
    pass

class EntityNotFoundError(PharmaTraceError):
    """Raised when an entity key cannot be resolved."""
    pass

class BrokenGenealogyError(PharmaTraceError):
    """Raised when a genealogy relationship foreign key is broken."""
    pass

class MassBalanceDiscrepancyError(PharmaTraceError):
    """Raised when production or delivery quantities violate mass balance."""
    pass

class QuarantineBreachError(PharmaTraceError):
    """Raised when a quarantined or recalled lot remains active for sale."""
    pass

class BlastRadiusLeakageError(PharmaTraceError):
    """Raised when an affected customer is missed during recall dispatch."""
    pass

class ValidationError(PharmaTraceError):
    """Raised when schema or rule constraints are violated."""
    pass

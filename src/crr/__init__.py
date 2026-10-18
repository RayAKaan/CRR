"""CRR reference implementation package."""

from crr.capability_api import router as _capability_router
from crr.transformation_api import router as _transformation_router

__version__ = "0.1.0"

# Register the Transformation router before Demand aggregates Capability routes.
_capability_router.include_router(_transformation_router)

del _capability_router, _transformation_router

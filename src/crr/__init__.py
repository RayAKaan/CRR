"""CRR reference implementation package."""

__version__ = "0.1.0"

# Register the Transformation router on the existing Capability router before
# the Demand API aggregates Capability routes into its application router.
from crr.capability_api import router as _capability_router
from crr.transformation_api import router as _transformation_router

_capability_router.include_router(_transformation_router)

del _capability_router, _transformation_router

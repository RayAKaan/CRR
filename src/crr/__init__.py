"""CRR reference implementation package."""

from crr.capability_api import router as _capability_router
from crr.routing_api import router as _routing_router
from crr.transformation_api import router as _transformation_router

__version__ = "0.1.0"

# Register routing and Transformation routers before Demand aggregates Capability routes.
_capability_router.include_router(_transformation_router)
_capability_router.include_router(_routing_router)

del _capability_router, _routing_router, _transformation_router

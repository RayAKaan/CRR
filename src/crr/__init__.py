"""CRR reference implementation package."""

from crr.capability_api import router as _capability_router
from crr.economic_api import router as _economic_router
from crr.routing_api import router as _routing_router
from crr.transformation_api import router as _transformation_router

__version__ = "0.1.0"

# Register routing, economics, and Transformation routers before Demand aggregates.
_capability_router.include_router(_transformation_router)
_capability_router.include_router(_routing_router)
_capability_router.include_router(_economic_router)

del _capability_router, _economic_router, _routing_router, _transformation_router

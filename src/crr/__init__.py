"""CRR reference implementation package."""

__version__ = "0.1.0"

# The existing application mounts the Demand router. Keep the Transformation
# router on that same aggregate without modifying the established API module.
from crr.demand_api import router as _demand_router
from crr.transformation_api import router as _transformation_router

_demand_router.include_router(_transformation_router)

del _demand_router, _transformation_router

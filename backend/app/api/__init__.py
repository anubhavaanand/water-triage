from .districts import router as districts_router
from .priority import router as priority_router
from .recurrence import router as recurrence_router
from .samples import router as samples_router
from .dashboard import router as dashboard_router
from .meta import router as meta_router
from .scoring import router as scoring_router
from .validation import router as validation_router

all_routers = [meta_router, dashboard_router, samples_router, districts_router, priority_router, recurrence_router, scoring_router, validation_router]

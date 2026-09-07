from .districts import router as districts_router
from .priority import router as priority_router
from .recurrence import router as recurrence_router
from .samples import router as samples_router
from .dashboard import router as dashboard_router

all_routers = [dashboard_router, samples_router, districts_router, priority_router, recurrence_router]

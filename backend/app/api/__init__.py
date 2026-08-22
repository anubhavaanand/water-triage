from .districts import router as districts_router
from .priority import router as priority_router
from .samples import router as samples_router

all_routers = [samples_router, districts_router, priority_router]

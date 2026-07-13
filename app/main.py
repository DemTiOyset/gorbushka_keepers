from fastapi import FastAPI

from app.audit.routers.audit_router import router as audit_router
from app.auth.routers.auth_routers import router as auth_router

app = FastAPI(title="Gorbushka Keepers Ozon", version="1.0.0")

app.include_router(audit_router)
app.include_router(auth_router)


@app.get("/")
def ping():
    return {"message": "OK"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit.routers import router as audit_router
from app.auth.routers import router as auth_router
from app.orders.routers import router as order_router
from app.users.routers import router as user_router

app = FastAPI(title="Gorbushka Keepers Ozon", version="1.0.0")

app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(order_router)


# Список разрешенных источников (origins)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:80",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # разрешить запросы с этих адресов
    allow_credentials=True,  # разрешить передачу кук/авторизационных заголовков
    allow_methods=["*"],  # разрешить все методы (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # разрешить все заголовки
)


@app.get("/")
def ping():
    return {"message": "OK"}

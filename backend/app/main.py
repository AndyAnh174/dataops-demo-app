from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="DataOps Demo API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.include_router(router)

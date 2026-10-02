from fastapi import FastAPI
from app.api.routes import router
from .dataset_generator_api import router as gen_router
app = FastAPI(title="Universal AI CI/CD Debugger (Groq)")
app.include_router(router)


app.include_router(gen_router)
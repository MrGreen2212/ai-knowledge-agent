import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.exceptions.handlers import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_startup_event():
    """Инициализация внешних ресурсов при старте."""
    from app.core.dependencies import get_storage_provider

    get_storage_provider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчик событий жизненного цикла FastAPI."""
    logger.info("Starting AI Knowledge Agent...")
    create_startup_event()
    yield
    logger.info("Shutting down AI Knowledge Agent...")


app = FastAPI(
    title="AI Knowledge Agent",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.get("/")
def read_root():
    return {"message": "AI Knowledge Agent"}


app.include_router(conversations_router)
app.include_router(documents_router)

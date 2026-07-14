from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.documents import router as documents_router


def create_startup_event():
    """Функция для инициализации внешних ресурсов при старте."""
    from app.services.storage import create_bucket
    create_bucket()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Современный обработчик событий жизненного цикла FastAPI.
    Выполняется один раз при запуске сервера.
    """
    create_startup_event()
    yield
    # Здесь можно будет добавить логику закрытия соединений при shutdown


app = FastAPI(
    title="AI Knowledge Agent",
    lifespan=lifespan  # Подключаем наш контекст
)


@app.get("/")
def read_root():
    return {
        "message": "AI Knowledge Agent"
    }

# Регистрируем роутер
app.include_router(documents_router)
from fastapi import FastAPI

app = FastAPI(
    title="AI Knowledge Agent",
    description="Personal AI knowledge assistant",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Knowledge Agent is running"
    }
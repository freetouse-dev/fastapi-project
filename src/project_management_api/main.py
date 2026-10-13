from fastapi import FastAPI

app = FastAPI(
    title="Project Management API",
    version="0.1.0",
    description="A collaborative project management REST API built with FastAPI.",
)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Project Management & Collaboration API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "project-management-api",
    }
"""Minimal M3 application; business capabilities are not implemented."""

from fastapi import FastAPI

app = FastAPI(title="M3 Maintenance")


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness without checking downstream dependencies."""
    return {"status": "ok"}

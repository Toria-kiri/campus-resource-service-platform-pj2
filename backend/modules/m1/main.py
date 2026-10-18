"""Minimal M1 application; business capabilities are not implemented."""

from fastapi import FastAPI

app = FastAPI(title="M1 Seat Reservation")


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness without checking downstream dependencies."""
    return {"status": "ok"}

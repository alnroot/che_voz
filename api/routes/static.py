from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["Static"])


@router.get("/")
async def root():
    """Redirect to the dialer interface"""
    return FileResponse("frontend/dialer.html")


@router.get("/dialer")
async def dialer():
    """Serve the dialer interface"""
    return FileResponse("frontend/dialer.html")


@router.get("/call")
async def call():
    """Serve the call interface"""
    return FileResponse("frontend/call-screen.html")
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["client"])

CLIENT_FILE = Path(__file__).resolve().parent.parent / "static" / "client.html"


@router.get("/client", response_class=FileResponse)
def read_client():
    return FileResponse(CLIENT_FILE)

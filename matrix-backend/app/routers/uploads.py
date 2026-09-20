from fastapi import APIRouter, UploadFile, File
from app.services.file_service import save_upload

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Used by all three upload surfaces in the UI (Source, Pattern, PYQs).
    Returns a file_id to reference from /api/generate."""
    file_id = save_upload(file)
    return {"file_id": file_id, "filename": file.filename}

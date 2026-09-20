from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models import GenerateRequest, GenerateResponse, QuestionPaper
from app.services.ai_client import chat_json, AIClientError
from app.services.file_service import extract_text, extract_text_many
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.services.pdf_generator import render_pdf, pdf_path

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_paper(req: GenerateRequest):
    # 1. Pull text out of whatever was uploaded at each step
    source_text = extract_text_many(req.source.uploaded_file_ids)
    pattern_text = extract_text_many(req.pattern.uploaded_file_ids)
    pyq_text = extract_text_many(req.pyq.uploaded_file_ids) if req.pyq.enabled else ""

    if not source_text and not req.source.search_query:
        raise HTTPException(
            status_code=400,
            detail="No source material — upload a file or provide a search query.",
        )
    if req.source.search_query and not source_text:
        # Placeholder: wire this to a real web-search + fetch pipeline.
        source_text = f"[Web search result placeholder for: '{req.source.search_query}'. " \
                       f"Replace this with real fetched content before production.]"

    # 2. Build the prompt and call MatrAIx-Persona-8B (or whichever endpoint is configured)
    user_prompt = build_user_prompt(req, source_text, pattern_text, pyq_text)
    try:
        raw = chat_json(SYSTEM_PROMPT, user_prompt, settings=req.model_settings)
        paper = QuestionPaper.model_validate(raw)
    except AIClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model returned an unexpected shape: {e}")

    # 3. Render to PDF
    pdf_file_id = render_pdf(paper, req.session_id)

    return GenerateResponse(
        session_id=req.session_id,
        paper=paper,
        pdf_url=f"/api/papers/{pdf_file_id}",
    )


@router.get("/papers/{file_id}")
async def get_paper_pdf(file_id: str):
    path = pdf_path(file_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    return FileResponse(path, media_type="application/pdf", filename=file_id)

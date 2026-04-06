from fastapi import APIRouter, HTTPException

from schemas.bible import BibleGenerateRequest
from utils.bible_api import (
    BibleAPIError,
    InvalidReferenceError,
    LANGUAGE_MODULE_MAP,
    PassageNotFoundError,
    fetch_bible_passage,
    generate_bible_text,
)

router = APIRouter(prefix="/bible", tags=["bible"])


@router.get("/lookup")
def bible_lookup(lang: str = "", reference: str = ""):
    if lang not in LANGUAGE_MODULE_MAP:
        raise HTTPException(status_code=400, detail="Unsupported language. Use ko, en, or ja.")

    normalized_reference = reference.strip()
    if not normalized_reference:
        raise HTTPException(status_code=400, detail="Reference is required.")

    try:
        return fetch_bible_passage(lang, normalized_reference)
    except PassageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BibleAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/generate")
def bible_generate(request: BibleGenerateRequest):
    try:
        return generate_bible_text(request.text)
    except InvalidReferenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PassageNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BibleAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

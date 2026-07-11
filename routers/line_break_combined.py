from fastapi import APIRouter
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_combined_line_break

router = APIRouter(prefix="/line-break/combined", tags=["line-break"])

@router.post('')
def line_break_combined(request: LineBreakRequest):
    entries = apply_combined_line_break(request.text)
    result = '\n\n\n'.join('\n\n'.join(parts) for _, parts in entries)
    return {'result': result}

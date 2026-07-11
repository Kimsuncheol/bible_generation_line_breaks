from fastapi import APIRouter
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_equals_line_break

router = APIRouter(prefix="/line-break/equals", tags=["line-break"])

@router.post('')
def line_break_equals(request: LineBreakRequest):
    result = apply_equals_line_break(request.text)
    return {'result': result}

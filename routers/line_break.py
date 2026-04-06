from fastapi import APIRouter
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_line_break, normalize

router = APIRouter(prefix="/line-break", tags=["line-break"])

@router.post('')
def line_break(request: LineBreakRequest):
    processed = normalize(request.text)
    result = apply_line_break(request.text)
    print('request: ', request.text)
    print('processed: ', processed)
    print('result: ', result)
    return {'result': result}

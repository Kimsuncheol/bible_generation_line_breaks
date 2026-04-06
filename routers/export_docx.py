import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from docx import Document
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_line_break, inspect_line_breaks

router = APIRouter(prefix="/line-break/export_docx", tags=["export"])

@router.post('')
def export_docx(request: LineBreakRequest):
    text = apply_line_break(request.text)
    _, _, lines = inspect_line_breaks(text)

    doc = Document()
    for line in lines:
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={'Content-Disposition': 'attachment; filename="output.docx"'},
    )

import io
import openpyxl
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_line_break

router = APIRouter(prefix="/line-break/export_xlsx", tags=["export"])

@router.post('')
def export_xlsx(request: LineBreakRequest):
    text = apply_line_break(request.text)
    lines = text.split('\n')

    wb = openpyxl.Workbook()
    ws = wb.active
    for line in lines:
        ws.append([line])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="output.xlsx"'},
    )

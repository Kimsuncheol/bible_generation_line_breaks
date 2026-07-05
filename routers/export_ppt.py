import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from schemas.line_break import LineBreakRequest
from utils.text_processing import apply_line_break, inspect_line_breaks

router = APIRouter(prefix="/line-break/export_ppt", tags=["export"])

FONT_NAME = "KoPubWorld바탕체 Bold"
FONT_SIZE = Pt(52)
BACKGROUND_COLOR = RGBColor(0x20, 0x38, 0x64)


def _set_east_asian_font(run, typeface):
    # run.font.name only sets the Latin typeface (a:latin); PowerPoint renders
    # CJK text using the separate East Asian typeface (a:ea), which python-pptx
    # has no high-level setter for.
    rPr = run.font._rPr
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", typeface)


@router.post('')
def export_ppt(request: LineBreakRequest):
    text = apply_line_break(request.text)
    text, _, _ = inspect_line_breaks(text)
    blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
    if not blocks:
        blocks = [text.strip()]

    prs = Presentation()
    blank_layout = prs.slide_layouts[6]

    for block in blocks:
        slide = prs.slides.add_slide(blank_layout)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = BACKGROUND_COLOR

        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(6))
        tf = txBox.text_frame
        tf.word_wrap = True

        lines = block.split('\n')
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = line
            run.font.size = FONT_SIZE
            run.font.name = FONT_NAME
            _set_east_asian_font(run, FONT_NAME)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        headers={'Content-Disposition': 'attachment; filename="output.pptx"'},
    )

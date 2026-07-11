from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Bible-verse slides: font weight comes from the font family itself (its name
# already ends in "Bold"), and the box is top-anchored, left-aligned text.
BIBLE_STYLE = {
    "font_name": "KoPubWorld바탕체 Bold",
    "font_size": Pt(52),
    "font_color": RGBColor(0xFF, 0xFF, 0xFF),
    "background_color": RGBColor(0x20, 0x38, 0x64),
}

# Outline ('=') slides: font weight is applied explicitly since "맑은 고딕" is a
# regular family name, and the box is vertically centered with selectable
# horizontal text alignment.
EQUALS_STYLE = {
    "font_name": "맑은 고딕",
    "font_size": Pt(60),
    "font_color": RGBColor(0xFF, 0xFF, 0xFF),
    "background_color": RGBColor(0x00, 0x00, 0x00),
}

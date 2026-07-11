from lxml import etree
from pptx.oxml.ns import qn


def set_east_asian_font(run, typeface):
    # run.font.name only sets the Latin typeface (a:latin); PowerPoint renders
    # CJK text using the separate East Asian typeface (a:ea), which python-pptx
    # has no high-level setter for.
    rPr = run.font._rPr
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", typeface)

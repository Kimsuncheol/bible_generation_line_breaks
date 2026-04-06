import io
from fastapi.testclient import TestClient
from pptx import Presentation
from docx import Document
import openpyxl
from main import app

client = TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────────

def test_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello FastAPI'}


# ── POST /line-break ──────────────────────────────────────────────────────────

class TestLineBreak:
    def test_single_verse(self):
        response = client.post('/line-break', json={'text': '창1:1 태초에 하나님이 천지를 창조하시니라'})
        assert response.status_code == 200
        assert response.json()['result'] == '창1:1\n태초에 하나님이 천지를 창조하시니라'

    def test_multiple_verses(self):
        text = '마20:7 이르되 우리를 품꾼으로 쓰는 이가 없음이니이다\n\n마20:8 저물매 포도원 주인이'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        result = response.json()['result']
        assert '마20:7\n이르되' in result
        assert '\n\n마20:8\n' in result
        assert '마20:8\n저물매' in result

    def test_single_newline_normalized_to_double(self):
        text = '마20:7 이르되 우리를 품꾼으로 쓰는 이가 없음이니이다\n마20:8 저물매 포도원 주인이'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        result = response.json()['result']
        assert '\n\n마20:8\n' in result

    def test_triple_newline_preserved(self):
        text = '마25:21 착하고 충성된 종아\n\n\n마25:29 무릇 있는 자는'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        result = response.json()['result']
        assert '\n\n\n마25:29\n' in result

    def test_footnote_not_broken(self):
        text = '요1:1 태초에 1)말씀이 계시니라 이 1)말씀이 하나님과 함께 계셨으니'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        result = response.json()['result']
        assert '요1:1\n태초에' in result
        assert '1)말씀이' in result
        assert '1)\n말씀이' not in result

    def test_no_digit_korean_boundary(self):
        text = '태초에 하나님이 천지를 창조하시니라'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        assert response.json()['result'] == text


# ── POST /line-break/export_ppt ──────────────────────────────────────────────

class TestExportPPT:
    def test_status_and_content_type(self):
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이'})
        assert response.status_code == 200
        assert 'presentationml' in response.headers['content-type']

    def test_content_disposition(self):
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이'})
        assert 'output.pptx' in response.headers['content-disposition']

    def test_slide_text_content(self):
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이 천지를 창조하시니라'})
        prs = Presentation(io.BytesIO(response.content))
        all_text = '\n'.join(
            shape.text_frame.text
            for slide in prs.slides
            for shape in slide.shapes
            if shape.has_text_frame
        )
        assert '창1:1' in all_text
        assert '태초에' in all_text

    def test_multiple_blocks_produce_multiple_slides(self):
        text = '창1:1 태초에 하나님이 천지를 창조하시니라\n\n창1:2 땅이 혼돈하고 공허하며'
        response = client.post('/line-break/export_ppt', json={'text': text})
        prs = Presentation(io.BytesIO(response.content))
        assert len(prs.slides) == 2


# ── POST /line-break/export_docx ─────────────────────────────────────────────

class TestExportDOCX:
    def test_status_and_content_type(self):
        response = client.post('/line-break/export_docx', json={'text': '창1:1 태초에 하나님이'})
        assert response.status_code == 200
        assert 'wordprocessingml' in response.headers['content-type']

    def test_content_disposition(self):
        response = client.post('/line-break/export_docx', json={'text': '창1:1 태초에 하나님이'})
        assert 'output.docx' in response.headers['content-disposition']

    def test_paragraph_content(self):
        response = client.post('/line-break/export_docx', json={'text': '창1:1 태초에 하나님이 천지를 창조하시니라'})
        doc = Document(io.BytesIO(response.content))
        paragraphs = [p.text for p in doc.paragraphs]
        assert '창1:1' in paragraphs
        assert '태초에 하나님이 천지를 창조하시니라' in paragraphs

    def test_each_line_is_own_paragraph(self):
        text = '창1:1 태초에 하나님이\n창1:2 땅이 혼돈하고'
        response = client.post('/line-break/export_docx', json={'text': text})
        doc = Document(io.BytesIO(response.content))
        paragraphs = [p.text for p in doc.paragraphs]
        assert '창1:1' in paragraphs
        assert '태초에 하나님이' in paragraphs
        assert '창1:2' in paragraphs
        assert '땅이 혼돈하고' in paragraphs


# ── POST /line-break/export_xlsx ─────────────────────────────────────────────

class TestExportXLSX:
    def test_status_and_content_type(self):
        response = client.post('/line-break/export_xlsx', json={'text': '창1:1 태초에 하나님이'})
        assert response.status_code == 200
        assert 'spreadsheetml' in response.headers['content-type']

    def test_content_disposition(self):
        response = client.post('/line-break/export_xlsx', json={'text': '창1:1 태초에 하나님이'})
        assert 'output.xlsx' in response.headers['content-disposition']

    def test_cell_content(self):
        response = client.post('/line-break/export_xlsx', json={'text': '창1:1 태초에 하나님이 천지를 창조하시니라'})
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        cell_values = [row[0].value for row in ws.iter_rows()]
        assert '창1:1' in cell_values
        assert '태초에 하나님이 천지를 창조하시니라' in cell_values

    def test_each_line_in_own_row(self):
        text = '창1:1 태초에 하나님이\n창1:2 땅이 혼돈하고'
        response = client.post('/line-break/export_xlsx', json={'text': text})
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        cell_values = [row[0].value for row in ws.iter_rows()]
        assert '창1:1' in cell_values
        assert '태초에 하나님이' in cell_values
        assert '창1:2' in cell_values
        assert '땅이 혼돈하고' in cell_values

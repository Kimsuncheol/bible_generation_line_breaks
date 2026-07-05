import io
import json
from unittest.mock import patch
from urllib.error import URLError

from fastapi.testclient import TestClient
from pptx import Presentation
from pptx.dml.color import RGBColor
from docx import Document
import openpyxl
from main import app
from utils.bible_api import BibleAPIError, generate_bible_text, normalize_korean_reference, parse_reference_lines
from utils.text_processing import inspect_line_breaks

client = TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────────

def test_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello FastAPI'}


def test_client_page():
    response = client.get('/client')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert '<html lang="en">' in response.text
    assert 'Line Break Test Client' in response.text
    assert 'line break' in response.text
    assert 'bible lookup' in response.text
    assert '/line-break/export_xlsx' in response.text
    assert '/bible/generate' in response.text
    assert 'Generate Bible Text' in response.text
    assert 'Output copied.' in response.text
    assert 'Bible' in response.text
    assert 'General Text' in response.text
    assert 'id="general-line-break-panel"' in response.text
    assert 'data-criterion="."' in response.text
    assert 'data-criterion=","' in response.text
    assert 'data-criterion="-"' in response.text
    assert 'Arabic number' in response.text
    assert 'Roman number' in response.text
    assert 'Chinese number' in response.text
    assert 'Bullet' in response.text
    assert 'Check mark' in response.text
    assert 'id="processGeneralBtn"' in response.text
    assert 'id="copyGeneralResultBtn"' in response.text
    assert 'id="copyResultBtn"' in response.text
    assert 'id="copyLookupBtn"' in response.text
    assert 'id="eraseSourceBtn"' in response.text
    assert 'id="eraseLookupInputBtn"' in response.text
    assert 'id="eraseResultBtn"' not in response.text
    assert 'id="eraseLookupResultBtn"' not in response.text
    assert 'height: 360px;' in response.text
    assert 'height: 260px;' in response.text
    assert 'resize: none;' in response.text
    assert 'overflow: auto;' in response.text
    assert 'scrollbar-width: none;' in response.text
    assert '-ms-overflow-style: none;' in response.text
    assert '::-webkit-scrollbar' in response.text
    assert 'display: none;' in response.text


def test_client_page_korean_query_locale():
    response = client.get('/client', params={'lang': 'ko'})
    assert response.status_code == 200
    assert '<html lang="ko">' in response.text
    assert '줄바꿈 테스트 클라이언트' in response.text
    assert '성경 본문 생성' in response.text
    assert '일반 텍스트' in response.text
    assert '기준' in response.text
    assert '아라비아 숫자' in response.text
    assert '체크 표시' in response.text
    assert '처리된 출력 복사' in response.text
    assert '일반 출력 복사' in response.text
    assert '출력이 복사되었습니다.' in response.text
    assert '/line-break/export_xlsx' in response.text
    assert '/bible/generate' in response.text


def test_client_page_korean_accept_language():
    response = client.get('/client', headers={'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'})
    assert response.status_code == 200
    assert '<html lang="ko">' in response.text
    assert '입력 텍스트' in response.text


def make_bible_payload(module: str, book_name: str, text: str):
    return {
        'results': [
            {
                'book_name': book_name,
                'verses': {
                    module: {
                        '3': {
                            '16': {
                                'chapter': 3,
                                'verse': 16,
                                'text': text,
                            }
                        }
                    }
                },
            }
        ]
    }


class MockHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return io.StringIO(json.dumps(self.payload))

    def __exit__(self, exc_type, exc, tb):
        return False


class TestBibleLookup:
    @patch('utils.bible_api.urlopen')
    def test_korean_lookup(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse(make_bible_payload('korean', '요한복음', '하나님이 세상을 이처럼 사랑하사'))
        response = client.get('/bible/lookup', params={'lang': 'ko', 'reference': '요 3:16'})
        assert response.status_code == 200
        data = response.json()
        assert data['lang'] == 'ko'
        assert data['module'] == 'korean'
        assert data['reference'] == '요 3:16'
        assert data['text'] == '하나님이 세상을 이처럼 사랑하사'
        assert data['verses'][0]['book'] == '요한복음'

    @patch('utils.bible_api.urlopen')
    def test_english_lookup(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse(make_bible_payload('web', 'John', 'For God so loved the world'))
        response = client.get('/bible/lookup', params={'lang': 'en', 'reference': 'John 3:16'})
        assert response.status_code == 200
        data = response.json()
        assert data['module'] == 'web'
        assert data['text'] == 'For God so loved the world'

    @patch('utils.bible_api.urlopen')
    def test_japanese_lookup(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse(make_bible_payload('kougo', 'ヨハネ', '神はそのひとり子をお与えになったほどに'))
        response = client.get('/bible/lookup', params={'lang': 'ja', 'reference': 'ヨハネ 3:16'})
        assert response.status_code == 200
        data = response.json()
        assert data['module'] == 'kougo'
        assert data['text'] == '神はそのひとり子をお与えになったほどに'

    def test_unsupported_language(self):
        response = client.get('/bible/lookup', params={'lang': 'fr', 'reference': 'Jean 3:16'})
        assert response.status_code == 400
        assert 'Unsupported language' in response.json()['detail']

    def test_missing_reference(self):
        response = client.get('/bible/lookup', params={'lang': 'en'})
        assert response.status_code == 400
        assert response.json()['detail'] == 'Reference is required.'

    def test_blank_reference(self):
        response = client.get('/bible/lookup', params={'lang': 'en', 'reference': '   '})
        assert response.status_code == 400
        assert response.json()['detail'] == 'Reference is required.'

    @patch('utils.bible_api.urlopen')
    def test_upstream_failure(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('network down')
        response = client.get('/bible/lookup', params={'lang': 'en', 'reference': 'John 3:16'})
        assert response.status_code == 502
        assert response.json()['detail'] == 'Failed to fetch passage from Bible SuperSearch.'

    @patch('utils.bible_api.urlopen')
    def test_no_verses_found(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse({'results': []})
        response = client.get('/bible/lookup', params={'lang': 'en', 'reference': 'Unknown 1:1'})
        assert response.status_code == 404
        assert response.json()['detail'] == 'No verses were returned for the given reference.'


class TestBibleReferenceParsing:
    def test_normalize_single_reference(self):
        parsed = normalize_korean_reference('마25:21')
        assert parsed['query_reference'] == '마태복음 25:21'
        assert parsed['display_reference'] == '마25:21'

    def test_normalize_range_reference(self):
        parsed = normalize_korean_reference('계2:8-13')
        assert parsed['query_reference'] == '요한계시록 2:8-13'
        assert parsed['display_reference'] == '계2:8-13'

    def test_normalize_pauline_reference(self):
        parsed = normalize_korean_reference('고전15:10')
        assert parsed['query_reference'] == '고린도전서 15:10'
        assert parsed['display_reference'] == '고전15:10'

    def test_parse_reference_lines_ignores_blank_and_deduplicates(self):
        input_count, parsed = parse_reference_lines('마25:21\n\n계2:8-13\n마25:21\n')
        assert input_count == 3
        assert [item['display_reference'] for item in parsed] == ['마25:21', '계2:8-13']

    def test_parse_reference_lines_extracts_single_parenthetical_reference(self):
        input_count, parsed = parse_reference_lines('(고전15:58)')
        assert input_count == 1
        assert [item['display_reference'] for item in parsed] == ['고전15:58']

    def test_parse_reference_lines_extracts_multiple_parenthetical_references(self):
        input_count, parsed = parse_reference_lines('(고전15:58)\n(대상6:31-32)')
        assert input_count == 2
        assert [item['display_reference'] for item in parsed] == ['고전15:58', '대상6:31-32']

    def test_parse_reference_lines_extracts_multiple_parens_on_one_line(self):
        input_count, parsed = parse_reference_lines('(고전15:58) (대상6:31-32)')
        assert input_count == 2
        assert [item['display_reference'] for item in parsed] == ['고전15:58', '대상6:31-32']


class TestBibleGeneration:
    @patch('utils.bible_api.fetch_bible_passage')
    def test_single_verse_generation(self, mock_fetch):
        mock_fetch.return_value = {
            'verses': [
                {'book': '마태복음', 'chapter': 25, 'verse': 21, 'text': '그 주인이 이르되'}
            ]
        }
        result = generate_bible_text('마25:21')
        assert result['input_count'] == 1
        assert result['unique_count'] == 1
        assert result['references'] == ['마25:21']
        assert result['output'] == '마25:21\n그 주인이 이르되'

    @patch('utils.bible_api.fetch_bible_passage')
    def test_range_generation_expands_per_verse(self, mock_fetch):
        mock_fetch.return_value = {
            'verses': [
                {'book': '요한계시록', 'chapter': 2, 'verse': 8, 'text': '서머나 교회의 사자에게'},
                {'book': '요한계시록', 'chapter': 2, 'verse': 9, 'text': '내가 네 환난과 궁핍을 아노니'},
            ]
        }
        result = generate_bible_text('계2:8-9')
        assert result['output'] == '계2:8\n서머나 교회의 사자에게\n\n계2:9\n내가 네 환난과 궁핍을 아노니'
        assert [item['output_reference'] for item in result['items']] == ['계2:8', '계2:9']

    @patch('utils.bible_api.fetch_bible_passage')
    def test_mixed_input_preserves_order_and_deduplicates(self, mock_fetch):
        def fake_fetch(lang, reference, timeout=15):
            mapping = {
                '마태복음 25:21': {
                    'verses': [{'book': '마태복음', 'chapter': 25, 'verse': 21, 'text': '잘 하였도다'}]
                },
                '이사야 43:7': {
                    'verses': [{'book': '이사야', 'chapter': 43, 'verse': 7, 'text': '내 이름으로 불려지는 모든 자'}]
                },
            }
            return mapping[reference]

        mock_fetch.side_effect = fake_fetch
        result = generate_bible_text('마25:21\n사43:7\n마25:21')
        assert result['input_count'] == 3
        assert result['unique_count'] == 2
        assert result['references'] == ['마25:21', '사43:7']
        assert result['output'] == '마25:21\n잘 하였도다\n\n사43:7\n내 이름으로 불려지는 모든 자'

    def test_invalid_reference_raises_400(self):
        response = client.post('/bible/generate', json={'text': '잘못된입력'})
        assert response.status_code == 400
        assert 'Unsupported or invalid reference' in response.json()['detail']

    @patch('utils.bible_api.fetch_bible_passage')
    def test_generate_endpoint_expands_range(self, mock_fetch):
        mock_fetch.return_value = {
            'verses': [
                {'book': '요한계시록', 'chapter': 2, 'verse': 8, 'text': '서머나 교회의 사자에게'},
                {'book': '요한계시록', 'chapter': 2, 'verse': 9, 'text': '내가 네 환난과 궁핍을 아노니'},
            ]
        }
        response = client.post('/bible/generate', json={'text': '계2:8-9'})
        assert response.status_code == 200
        data = response.json()
        assert data['references'] == ['계2:8-9']
        assert data['items'][0]['output_reference'] == '계2:8'
        assert data['items'][1]['output_reference'] == '계2:9'

    @patch('utils.bible_api.fetch_bible_passage')
    def test_generate_endpoint_upstream_failure(self, mock_fetch):
        mock_fetch.side_effect = BibleAPIError('Failed to fetch passage from Bible SuperSearch.')
        response = client.post('/bible/generate', json={'text': '마25:21'})
        assert response.status_code == 502


# ── utils.text_processing.inspect_line_breaks ────────────────────────────────

class TestInspectLineBreaks:
    def test_no_line_break(self):
        normalized, has_line_breaks, lines = inspect_line_breaks('창1:1 태초에 하나님이')
        assert normalized == '창1:1 태초에 하나님이'
        assert has_line_breaks is False
        assert lines == ['창1:1 태초에 하나님이']

    def test_unix_line_break(self):
        normalized, has_line_breaks, lines = inspect_line_breaks('창1:1\n태초에 하나님이')
        assert normalized == '창1:1\n태초에 하나님이'
        assert has_line_breaks is True
        assert lines == ['창1:1', '태초에 하나님이']

    def test_windows_line_break(self):
        normalized, has_line_breaks, lines = inspect_line_breaks('창1:1\r\n태초에 하나님이')
        assert normalized == '창1:1\n태초에 하나님이'
        assert has_line_breaks is True
        assert lines == ['창1:1', '태초에 하나님이']

    def test_old_mac_line_break(self):
        normalized, has_line_breaks, lines = inspect_line_breaks('창1:1\r태초에 하나님이')
        assert normalized == '창1:1\n태초에 하나님이'
        assert has_line_breaks is True
        assert lines == ['창1:1', '태초에 하나님이']


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

    def test_parenthetical_content_after_reference(self):
        text = '눅23:51 (그들의 결의와 행사에 찬성하지 아니한 자라) 그는 유대인의 동네 아리마대 사람이요 하나님의 나라를 기다리는 자라'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        assert response.json()['result'] == (
            '눅23:51\n'
            '(그들의 결의와 행사에 찬성하지 아니한 자라) 그는 유대인의 동네 아리마대 사람이요 하나님의 나라를 기다리는 자라'
        )

    def test_no_digit_korean_boundary(self):
        text = '태초에 하나님이 천지를 창조하시니라'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        assert response.json()['result'] == text

    def test_windows_newline_normalized(self):
        text = '마20:7 이르되 우리를 품꾼으로 쓰는 이가 없음이니이다\r\n마20:8 저물매 포도원 주인이'
        response = client.post('/line-break', json={'text': text})
        assert response.status_code == 200
        result = response.json()['result']
        assert '\r' not in result
        assert '\n\n마20:8\n' in result


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

    def test_windows_double_newline_produces_multiple_slides(self):
        text = '창1:1 태초에 하나님이 천지를 창조하시니라\r\n\r\n창1:2 땅이 혼돈하고 공허하며'
        response = client.post('/line-break/export_ppt', json={'text': text})
        prs = Presentation(io.BytesIO(response.content))
        assert len(prs.slides) == 2

    def test_font_size_and_name_applied(self):
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이'})
        prs = Presentation(io.BytesIO(response.content))
        run = prs.slides[0].shapes[0].text_frame.paragraphs[0].runs[0]
        assert run.font.size.pt == 52
        assert run.font.name == 'KoPubWorld바탕체 Bold'

    def test_east_asian_font_applied(self):
        from pptx.oxml.ns import qn
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이'})
        prs = Presentation(io.BytesIO(response.content))
        run = prs.slides[0].shapes[0].text_frame.paragraphs[0].runs[0]
        ea = run.font._rPr.find(qn('a:ea'))
        assert ea is not None
        assert ea.get('typeface') == 'KoPubWorld바탕체 Bold'

    def test_slide_background_color_applied(self):
        response = client.post('/line-break/export_ppt', json={'text': '창1:1 태초에 하나님이'})
        prs = Presentation(io.BytesIO(response.content))
        background = prs.slides[0].background
        assert background.fill.fore_color.rgb == RGBColor(0x20, 0x38, 0x64)


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

    def test_windows_line_breaks_become_paragraphs(self):
        text = '창1:1 태초에 하나님이\r\n창1:2 땅이 혼돈하고'
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

    def test_windows_line_breaks_become_rows(self):
        text = '창1:1 태초에 하나님이\r\n창1:2 땅이 혼돈하고'
        response = client.post('/line-break/export_xlsx', json={'text': text})
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        cell_values = [row[0].value for row in ws.iter_rows()]
        assert '창1:1' in cell_values
        assert '태초에 하나님이' in cell_values
        assert '창1:2' in cell_values
        assert '땅이 혼돈하고' in cell_values

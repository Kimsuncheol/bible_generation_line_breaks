import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


API_URL = "https://api.biblesupersearch.com/api"
LANGUAGE_MODULE_MAP = {
    "ko": "korean",
    "en": "web",
    "ja": "kougo",
}

KOREAN_BOOK_ALIASES = {
    "창": ("창세기", "창"),
    "창세기": ("창세기", "창"),
    "출": ("출애굽기", "출"),
    "출애굽기": ("출애굽기", "출"),
    "레": ("레위기", "레"),
    "레위기": ("레위기", "레"),
    "민": ("민수기", "민"),
    "민수기": ("민수기", "민"),
    "신": ("신명기", "신"),
    "신명기": ("신명기", "신"),
    "수": ("여호수아", "수"),
    "여호수아": ("여호수아", "수"),
    "삿": ("사사기", "삿"),
    "사사기": ("사사기", "삿"),
    "룻": ("룻기", "룻"),
    "룻기": ("룻기", "룻"),
    "삼상": ("사무엘상", "삼상"),
    "사무엘상": ("사무엘상", "삼상"),
    "삼하": ("사무엘하", "삼하"),
    "사무엘하": ("사무엘하", "삼하"),
    "왕상": ("열왕기상", "왕상"),
    "열왕기상": ("열왕기상", "왕상"),
    "왕하": ("열왕기하", "왕하"),
    "열왕기하": ("열왕기하", "왕하"),
    "대상": ("역대상", "대상"),
    "역대상": ("역대상", "대상"),
    "대하": ("역대하", "대하"),
    "역대하": ("역대하", "대하"),
    "스": ("에스라", "스"),
    "에스라": ("에스라", "스"),
    "느": ("느헤미야", "느"),
    "느헤미야": ("느헤미야", "느"),
    "에": ("에스더", "에"),
    "에스더": ("에스더", "에"),
    "욥": ("욥기", "욥"),
    "욥기": ("욥기", "욥"),
    "시": ("시편", "시"),
    "시편": ("시편", "시"),
    "잠": ("잠언", "잠"),
    "잠언": ("잠언", "잠"),
    "전": ("전도서", "전"),
    "전도서": ("전도서", "전"),
    "아": ("아가", "아"),
    "아가": ("아가", "아"),
    "사": ("이사야", "사"),
    "이사야": ("이사야", "사"),
    "렘": ("예레미야", "렘"),
    "예레미야": ("예레미야", "렘"),
    "애": ("예레미야애가", "애"),
    "예레미야애가": ("예레미야애가", "애"),
    "겔": ("에스겔", "겔"),
    "에스겔": ("에스겔", "겔"),
    "단": ("다니엘", "단"),
    "다니엘": ("다니엘", "단"),
    "호": ("호세아", "호"),
    "호세아": ("호세아", "호"),
    "욜": ("요엘", "욜"),
    "요엘": ("요엘", "욜"),
    "암": ("아모스", "암"),
    "아모스": ("아모스", "암"),
    "옵": ("오바댜", "옵"),
    "오바댜": ("오바댜", "옵"),
    "욘": ("요나", "욘"),
    "요나": ("요나", "욘"),
    "미": ("미가", "미"),
    "미가": ("미가", "미"),
    "나": ("나훔", "나"),
    "나훔": ("나훔", "나"),
    "합": ("하박국", "합"),
    "하박국": ("하박국", "합"),
    "습": ("스바냐", "습"),
    "스바냐": ("스바냐", "습"),
    "학": ("학개", "학"),
    "학개": ("학개", "학"),
    "슥": ("스가랴", "슥"),
    "스가랴": ("스가랴", "슥"),
    "말": ("말라기", "말"),
    "말라기": ("말라기", "말"),
    "마": ("마태복음", "마"),
    "마태복음": ("마태복음", "마"),
    "막": ("마가복음", "막"),
    "마가복음": ("마가복음", "막"),
    "눅": ("누가복음", "눅"),
    "누가복음": ("누가복음", "눅"),
    "요": ("요한복음", "요"),
    "요한복음": ("요한복음", "요"),
    "행": ("사도행전", "행"),
    "사도행전": ("사도행전", "행"),
    "롬": ("로마서", "롬"),
    "로마서": ("로마서", "롬"),
    "고전": ("고린도전서", "고전"),
    "고린도전서": ("고린도전서", "고전"),
    "고후": ("고린도후서", "고후"),
    "고린도후서": ("고린도후서", "고후"),
    "갈": ("갈라디아서", "갈"),
    "갈라디아서": ("갈라디아서", "갈"),
    "엡": ("에베소서", "엡"),
    "에베소서": ("에베소서", "엡"),
    "빌": ("빌립보서", "빌"),
    "빌립보서": ("빌립보서", "빌"),
    "골": ("골로새서", "골"),
    "골로새서": ("골로새서", "골"),
    "살전": ("데살로니가전서", "살전"),
    "데살로니가전서": ("데살로니가전서", "살전"),
    "살후": ("데살로니가후서", "살후"),
    "데살로니가후서": ("데살로니가후서", "살후"),
    "딤전": ("디모데전서", "딤전"),
    "디모데전서": ("디모데전서", "딤전"),
    "딤후": ("디모데후서", "딤후"),
    "디모데후서": ("디모데후서", "딤후"),
    "딛": ("디도서", "딛"),
    "디도서": ("디도서", "딛"),
    "몬": ("빌레몬서", "몬"),
    "빌레몬서": ("빌레몬서", "몬"),
    "히": ("히브리서", "히"),
    "히브리서": ("히브리서", "히"),
    "약": ("야고보서", "약"),
    "야고보서": ("야고보서", "약"),
    "벧전": ("베드로전서", "벧전"),
    "베드로전서": ("베드로전서", "벧전"),
    "벧후": ("베드로후서", "벧후"),
    "베드로후서": ("베드로후서", "벧후"),
    "요일": ("요한일서", "요일"),
    "요한일서": ("요한일서", "요일"),
    "요이": ("요한이서", "요이"),
    "요한이서": ("요한이서", "요이"),
    "요삼": ("요한삼서", "요삼"),
    "요한삼서": ("요한삼서", "요삼"),
    "유": ("유다서", "유"),
    "유다서": ("유다서", "유"),
    "계": ("요한계시록", "계"),
    "요한계시록": ("요한계시록", "계"),
}
KOREAN_BOOK_KEYS = sorted(KOREAN_BOOK_ALIASES, key=len, reverse=True)


class BibleAPIError(Exception):
    pass


class PassageNotFoundError(BibleAPIError):
    pass


class InvalidReferenceError(BibleAPIError):
    pass


def _extract_verses(payload: dict, module: str) -> list[dict]:
    verses = []

    for result in payload.get("results", []):
        book_name = result.get("book_name") or result.get("book_short") or ""
        module_verses = result.get("verses", {}).get(module, {})

        for chapter_key, chapter_verses in module_verses.items():
            for verse_key, verse_data in chapter_verses.items():
                text = (verse_data.get("text") or "").strip()
                if not text:
                    continue

                verses.append(
                    {
                        "book": book_name,
                        "chapter": int(verse_data.get("chapter", chapter_key)),
                        "verse": int(verse_data.get("verse", verse_key)),
                        "text": text,
                    }
                )

    return verses


def _fetch_payload(module: str, reference: str, timeout: int = 15) -> dict:
    query = urlencode({"bible": module, "reference": reference})
    url = f"{API_URL}?{query}"

    try:
        with urlopen(url, timeout=timeout) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BibleAPIError("Failed to fetch passage from Bible SuperSearch.") from exc


def fetch_bible_passage(lang: str, reference: str, timeout: int = 15) -> dict:
    module = LANGUAGE_MODULE_MAP[lang]
    payload = _fetch_payload(module, reference, timeout=timeout)
    verses = _extract_verses(payload, module)
    if not verses:
        raise PassageNotFoundError("No verses were returned for the given reference.")

    return {
        "lang": lang,
        "module": module,
        "reference": reference,
        "text": "\n".join(verse["text"] for verse in verses),
        "verses": verses,
        "source": {
            "name": "Bible SuperSearch",
            "url": API_URL,
            "module": module,
        },
    }


def _match_book_alias(normalized: str) -> tuple[str, str, str]:
    for alias in KOREAN_BOOK_KEYS:
        if normalized.startswith(alias):
            book_name, abbreviation = KOREAN_BOOK_ALIASES[alias]
            return alias, book_name, abbreviation
    raise InvalidReferenceError(f"Unsupported or invalid reference: {normalized}")


def normalize_korean_reference(reference: str) -> dict:
    cleaned = re.sub(r"\s+", "", reference)
    if not cleaned:
        raise InvalidReferenceError("Reference is required.")

    alias, book_name, abbreviation = _match_book_alias(cleaned)
    remainder = cleaned[len(alias):]
    match = re.fullmatch(r"(\d+):(\d+)(?:-(\d+))?", remainder)
    if not match:
        raise InvalidReferenceError(f"Unsupported or invalid reference: {reference}")

    chapter = int(match.group(1))
    start_verse = int(match.group(2))
    end_verse = int(match.group(3) or start_verse)
    if end_verse < start_verse:
        raise InvalidReferenceError(f"Unsupported or invalid reference: {reference}")

    canonical = f"{book_name} {chapter}:{start_verse}"
    display = f"{abbreviation}{chapter}:{start_verse}"
    if end_verse != start_verse:
        canonical = f"{canonical}-{end_verse}"
        display = f"{display}-{end_verse}"

    return {
        "input_reference": reference.strip(),
        "book_name": book_name,
        "book_abbreviation": abbreviation,
        "chapter": chapter,
        "start_verse": start_verse,
        "end_verse": end_verse,
        "canonical_reference": canonical,
        "query_reference": canonical,
        "display_reference": display,
    }


def parse_reference_lines(text: str) -> tuple[int, list[dict]]:
    raw_lines = [line.strip() for line in text.splitlines()]
    references = [line for line in raw_lines if line]
    seen = set()
    unique_references = []

    for line in references:
        parsed = normalize_korean_reference(line)
        if parsed["canonical_reference"] in seen:
            continue
        seen.add(parsed["canonical_reference"])
        unique_references.append(parsed)

    return len(references), unique_references


def generate_bible_text(text: str, timeout: int = 15) -> dict:
    input_count, references = parse_reference_lines(text)
    items = []

    if not references:
        raise InvalidReferenceError("Reference is required.")

    for reference in references:
        payload = fetch_bible_passage("ko", reference["query_reference"], timeout=timeout)
        verses = payload["verses"]
        for verse in verses:
            items.append(
                {
                    "input_reference": reference["input_reference"],
                    "normalized_reference": reference["query_reference"],
                    "output_reference": f'{reference["book_abbreviation"]}{verse["chapter"]}:{verse["verse"]}',
                    "text": verse["text"],
                }
            )

    output = "\n\n".join(f'{item["output_reference"]}\n{item["text"]}' for item in items)

    return {
        "input_count": input_count,
        "unique_count": len(references),
        "references": [reference["display_reference"] for reference in references],
        "output": output,
        "items": items,
    }

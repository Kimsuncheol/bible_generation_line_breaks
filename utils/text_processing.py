import json
import re
from pathlib import Path

from utils.bible_api import KOREAN_BOOK_ALIASES

def inspect_line_breaks(text: str) -> tuple[str, bool, list[str]]:
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    has_line_breaks = '\n' in normalized
    return normalized, has_line_breaks, normalized.splitlines()

def normalize(text: str) -> str:
    text, _, _ = inspect_line_breaks(text)
    # Upgrade lone \n before verse ref to \n\n; preserve \n\n and \n\n\n
    return re.sub(r'(?<!\n)\n(?!\n)([가-힣]+\d+:\d)', r'\n\n\1', text)

def apply_line_break(text: str) -> str:
    # Step 1: normalize verse separators
    result = normalize(text)
    # Step 2: insert \n between verse-ref number and Korean content
    result = re.sub(r'(^|\n)([가-힣]+\d+:\d+(?:-\d+)?)[ \t]+', r'\1\2\n', result)
    return result

def apply_equals_line_break(text: str) -> str:
    # Each non-blank source line becomes its own block (slide); within a
    # block, break after every '=' since it marks the outline/answer boundary.
    _, _, lines = inspect_line_breaks(text)
    blocks = [re.sub(r'=', '=\n', line.strip()) for line in lines if line.strip()]
    return '\n\n'.join(blocks)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CATALOG_FILES = (
    _PROJECT_ROOT / 'old_testament_expanded.json',
    _PROJECT_ROOT / 'new_testament_expanded.json',
)
# The supplied expanded JSON files contain three non-standard keys. Normalize them
# at the data boundary so the rest of the parser uses the established Korean
# abbreviations from KOREAN_BOOK_ALIASES.
_CATALOG_KEY_ALIASES = {'누': '눅', '야': '약', '하': '합'}


def _load_bible_catalog() -> dict[str, frozenset[int]]:
    catalog: dict[str, frozenset[int]] = {}
    for path in _CATALOG_FILES:
        with path.open(encoding='utf-8') as file:
            books = json.load(file)
        for raw_book, chapters in books.items():
            book = _CATALOG_KEY_ALIASES.get(raw_book, raw_book)
            catalog[book] = frozenset(int(chapter) for chapter in chapters)
    return catalog


BIBLE_CATALOG = _load_bible_catalog()
BOOK_ALIAS_TO_ABBREVIATION = {
    alias: abbreviation
    for alias, (_, abbreviation) in KOREAN_BOOK_ALIASES.items()
}
_BOOK_PATTERN = '|'.join(
    re.escape(alias) for alias in sorted(BOOK_ALIAS_TO_ABBREVIATION, key=len, reverse=True)
)
_REFERENCE_CORE = (
    rf'(?P<book>{_BOOK_PATTERN})\s*'
    r'(?P<chapter>\d+)\s*(?::|장\s*)\s*'
    r'(?P<start_verse>\d+)\s*(?:절)?'
    r'(?:\s*[-~〜–—]\s*(?P<end_verse>\d+)\s*(?:절)?)?'
)
REFERENCE_PATTERN = re.compile(rf'^{_REFERENCE_CORE}$')
BIBLE_LINE_PATTERN = re.compile(rf'^(?P<reference>{_REFERENCE_CORE})[ \t]+(?P<content>.+)$')
REF_PARTS_PATTERN = re.compile(r'^([가-힣]+)(\d+):(\d+)')
CITATION_PATTERN = re.compile(r'\(([^()]+)\)\s*$')
# A plain text starts with an ordinal marker ('첫째', '둘째', ...) or a
# numbered-list marker ('1.', '1)'); a bare '=' elsewhere in a line is not
# enough on its own (e.g. a stray '=' in a header shouldn't be misread).
PLAIN_TEXT_PATTERN = re.compile(r'^([가-힣]+째|\d+[.)])')


def parse_bible_reference(reference: str) -> dict | None:
    """Parse and catalog-validate a Korean Bible reference."""
    match = REFERENCE_PATTERN.fullmatch(reference.strip())
    if not match:
        return None

    book = BOOK_ALIAS_TO_ABBREVIATION[match.group('book')]
    chapter = int(match.group('chapter'))
    start_verse = int(match.group('start_verse'))
    end_verse = int(match.group('end_verse') or start_verse)
    if chapter not in BIBLE_CATALOG.get(book, ()):
        return None
    if start_verse < 1 or end_verse < start_verse:
        return None

    canonical_reference = f'{book}{chapter}:{start_verse}'
    if end_verse != start_verse:
        canonical_reference += f'~{end_verse}'
    return {
        'book': book,
        'book_name': KOREAN_BOOK_ALIASES[match.group('book')][0],
        'chapter': chapter,
        'start_verse': start_verse,
        'end_verse': end_verse,
        'canonical_reference': canonical_reference,
    }


def parse_bible_line(line: str) -> tuple[str, str] | None:
    """Return a canonical reference and verse text for a valid Bible line."""
    match = BIBLE_LINE_PATTERN.fullmatch(line.strip())
    if not match:
        return None
    parsed = parse_bible_reference(match.group('reference'))
    if not parsed:
        return None
    return parsed['canonical_reference'], match.group('content').strip()


def _group_citation_key(group: list[tuple[str, str]]) -> str | None:
    # Mirrors how an outline line cites a range, e.g. a 막16:16 + 막16:17
    # group is cited as '막16:16~17'; a single-verse group as '고후8:9'.
    first_match = REF_PARTS_PATTERN.match(group[0][0])
    if not first_match:
        return None
    book, chapter, first_verse = first_match.group(1), first_match.group(2), first_match.group(3)
    if len(group) == 1:
        return group[0][0]
    last_match = REF_PARTS_PATTERN.match(group[-1][0])
    last_verse = last_match.group(3) if last_match else first_verse
    return f'{book}{chapter}:{first_verse}~{last_verse}'


def _format_bible_group(group: list[tuple[str, str]]) -> list[str]:
    # One string per verse: verses cited together (e.g. '막16:16~17') stay
    # adjacent in text output but still become separate slides in PPT export.
    return [f'{ref}\n{content}' if content else ref for ref, content in group]


def apply_combined_line_break(text: str) -> list[tuple[str, list[str]]]:
    # Parses the whole document into ordered 'bible' verse groups (consecutive
    # verse lines separated by at most one blank line) and plain-text outline
    # lines (start with an ordinal/list marker); any other non-blank line
    # (e.g. a '♡본론' section header) is dropped.
    # Each returned entry's parts list holds one string per resulting slide;
    # callers that want flat text should join a bible entry's parts with a
    # single blank line and join entries themselves with a wider gap.
    _, _, lines = inspect_line_breaks(text)

    raw_items: list[tuple[str, object]] = []
    current_group: list[tuple[str, str]] = []
    blank_run = 0

    def flush_group():
        nonlocal current_group
        if current_group:
            raw_items.append(('bible', current_group))
            current_group = []

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        stripped = line.strip()
        if not stripped:
            blank_run += 1
            line_index += 1
            continue

        bible_line = parse_bible_line(stripped)
        reference_only = parse_bible_reference(stripped)
        if bible_line or reference_only:
            if bible_line:
                reference, content = bible_line
            else:
                reference = reference_only['canonical_reference']
                content = ''
                # Bible lookup output uses two physical lines: a reference on
                # one line and its verse text on the immediately following
                # line. Consume that line only when it is not another known
                # structural line.
                if line_index + 1 < len(lines):
                    candidate = lines[line_index + 1].strip()
                    if (
                        candidate
                        and not parse_bible_line(candidate)
                        and not parse_bible_reference(candidate)
                        and not PLAIN_TEXT_PATTERN.match(candidate)
                    ):
                        content = candidate
                        line_index += 1

            if current_group and blank_run <= 1:
                current_group.append((reference, content))
            else:
                flush_group()
                current_group = [(reference, content)]
            blank_run = 0
            line_index += 1
            continue

        flush_group()
        blank_run = 0
        if PLAIN_TEXT_PATTERN.match(stripped):
            raw_items.append(('outline', stripped))
        # else: a header/noise line (e.g. '♡본론'), dropped.
        line_index += 1

    flush_group()

    # Outline lines cite a verse (range) by its trailing '(...)'; resolve each
    # citation to its bible group up front so we can suppress duplicates when
    # the group's own position is later re-visited during emission.
    groups_by_key: dict[str, list[tuple[str, object]]] = {}
    for item in raw_items:
        if item[0] == 'bible':
            key = _group_citation_key(item[1])
            if key:
                groups_by_key.setdefault(key, []).append(item)

    consumed_ids = set()
    outline_pairs = {}
    for item in raw_items:
        if item[0] != 'outline':
            continue
        citation_match = CITATION_PATTERN.search(item[1])
        if not citation_match:
            continue
        parsed_citation = parse_bible_reference(citation_match.group(1))
        citation_key = parsed_citation['canonical_reference'] if parsed_citation else citation_match.group(1)
        candidates = [g for g in groups_by_key.get(citation_key, []) if id(g) not in consumed_ids]
        if candidates:
            group_item = candidates[0]
            consumed_ids.add(id(group_item))
            outline_pairs[id(item)] = group_item

    result: list[tuple[str, list[str]]] = []
    for item in raw_items:
        if item[0] == 'outline':
            result.append(('equals', [re.sub(r'=', '=\n', item[1])]))
            matched = outline_pairs.get(id(item))
            if matched:
                result.append(('bible', _format_bible_group(matched[1])))
        elif id(item) not in consumed_ids:
            result.append(('bible', _format_bible_group(item[1])))

    return result

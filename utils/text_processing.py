import re

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

BIBLE_LINE_PATTERN = re.compile(r'^([가-힣]+\d+:\d+(?:-\d+)?)[ \t]+(.+)$')
REF_PARTS_PATTERN = re.compile(r'^([가-힣]+)(\d+):(\d+)')
CITATION_PATTERN = re.compile(r'\(([^()]+)\)\s*$')
# A plain text starts with an ordinal marker ('첫째', '둘째', ...) or a
# numbered-list marker ('1.', '1)'); a bare '=' elsewhere in a line is not
# enough on its own (e.g. a stray '=' in a header shouldn't be misread).
PLAIN_TEXT_PATTERN = re.compile(r'^([가-힣]+째|\d+[.)])')

def _group_citation_key(group: list[tuple[str, str]]) -> str | None:
    # Mirrors how an outline line cites a range, e.g. a 막16:16 + 막16:17
    # group is cited as '막16:16~17'; a single-verse group as '고후8:9'.
    first_match = REF_PARTS_PATTERN.match(group[0][0])
    if not first_match:
        return None
    book, chapter, first_verse = first_match.group(1), first_match.group(2), first_match.group(3)
    if len(group) == 1:
        return f'{book}{chapter}:{first_verse}'
    last_match = REF_PARTS_PATTERN.match(group[-1][0])
    last_verse = last_match.group(3) if last_match else first_verse
    return f'{book}{chapter}:{first_verse}~{last_verse}'

def _format_bible_group(group: list[tuple[str, str]]) -> list[str]:
    # One string per verse: verses cited together (e.g. '막16:16~17') stay
    # adjacent in text output but still become separate slides in PPT export.
    return [f'{ref}\n{content}' for ref, content in group]

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

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_run += 1
            continue

        bible_match = BIBLE_LINE_PATTERN.match(stripped)
        if bible_match:
            if current_group and blank_run <= 1:
                current_group.append((bible_match.group(1), bible_match.group(2)))
            else:
                flush_group()
                current_group = [(bible_match.group(1), bible_match.group(2))]
            blank_run = 0
            continue

        flush_group()
        blank_run = 0
        if PLAIN_TEXT_PATTERN.match(stripped):
            raw_items.append(('outline', stripped))
        # else: a header/noise line (e.g. '♡본론'), dropped.

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
        candidates = [g for g in groups_by_key.get(citation_match.group(1), []) if id(g) not in consumed_ids]
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

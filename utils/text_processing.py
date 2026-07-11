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

def classify_combined_line(line: str) -> tuple[str, str]:
    # A line is 'bible' when it starts with a verse reference (e.g. '롬10:17
    # ...'); anything else (e.g. an outline line using '=') is 'equals'.
    match = BIBLE_LINE_PATTERN.match(line.strip())
    if match:
        return 'bible', f'{match.group(1)}\n{match.group(2)}'
    return 'equals', re.sub(r'=', '=\n', line.strip())

def apply_combined_line_break(text: str) -> list[tuple[str, str]]:
    # Each non-blank source line becomes its own slide/block, classified and
    # broken independently so Bible verses and '=' outline lines can mix.
    _, _, lines = inspect_line_breaks(text)
    return [classify_combined_line(line) for line in lines if line.strip()]

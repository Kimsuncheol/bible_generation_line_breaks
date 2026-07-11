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

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
    result = re.sub(r'(\d)(?!\))[ ]+([가-힣])', r'\1\n\2', result)
    return result

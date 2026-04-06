import re

def normalize(text: str) -> str:
    # Upgrade lone \n before verse ref to \n\n; preserve \n\n and \n\n\n
    return re.sub(r'(?<!\n)\n(?!\n)([가-힣]+\d+:\d)', r'\n\n\1', text)

def apply_line_break(text: str) -> str:
    # Step 1: normalize verse separators
    result = normalize(text)
    # Step 2: insert \n between verse-ref number and Korean content
    result = re.sub(r'(\d)(?!\))[ ]+([가-힣])', r'\1\n\2', result)
    return result

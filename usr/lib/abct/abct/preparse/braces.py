# abct/preparse/braces.py

import re

def _get_indent(line: str, tab_size: int = 4) -> int:
    """Calculates the indentation level by expanding tabs ONLY in leading whitespace."""
    leading_whitespace = line[:len(line) - len(line.lstrip())]
    return len(leading_whitespace.expandtabs(tab_size))

def _handle_semicolon(code: str, line_num: int) -> str:
    """
    Automatically appends a semicolon to statements that require one.
    Skipped for lines ending in ';', '{', ':', or empty/metadata lines.
    """
    stripped = code.strip()
    
    # 1. Skip empty lines or pure whitespace
    if not stripped:
        return code
        
    # 2. Skip structural markers that don't take semicolons
    if stripped.endswith((';', '{', ':')):
        return code
        
    # Otherwise, safely append the semicolon
    # rstrip() ensures we place the semicolon right after the text, before newlines
    return code.rstrip() + ";"


def colon_to_braces(src: str) -> str:
    lines = src.splitlines()
    out = []
    stack = [0] # indent levels
    indent_size = None
    in_string = None # None, "'", '"', '"""', "'''"

    def strip_comment(s):
        # Remove unquoted #
        in_sq = in_dq = False
        for i, c in enumerate(s):
            if c == "'" and not in_dq:
                in_sq = not in_sq
            elif c == '"' and not in_sq:
                in_dq = not in_dq
            elif c == '#' and not in_sq and not in_dq:
                return s[:i].rstrip()
        return s.rstrip()

    for idx, raw in enumerate(lines, start=1):
        if not raw.strip():
            out.append(raw)
            continue

        # Track indent
        indent = _get_indent(raw)
        code = strip_comment(raw)
        # Detect indent size from first indented line
        if indent_size is None and indent > 0:
            indent_size = indent

        # Close blocks for dedents
        while indent < stack[-1]:
            stack.pop()
            out.append(" " * stack[-1] + "}")

        # Check if line ends with : outside strings
        if code.rstrip().endswith(":"):
            # Don't convert for lambda, slice, dict
            if not re.search(r'\b(lambda|slice)\s*:', code) and not re.search(r'[{,]\s*:', code):
                # Replace only the last : with {
                new_line = re.sub(r':\s*$', ' {', raw.rstrip())
                out.append(new_line)
                stack.append(indent + (indent_size or 4))
                continue

        raw = _handle_semicolon(raw, line_num=idx)

        out.append(raw)

    # Close remaining blocks
    while len(stack) > 1:
        stack.pop()
        out.append(" " * stack[-1] + "}")

    return "\n".join(out)

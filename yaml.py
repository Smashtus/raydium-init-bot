from __future__ import annotations
from typing import Any, Dict, List, Tuple

def safe_load(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, result)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith('#'):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        while stack and indent < stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        key, _, value = raw_line.strip().partition(':')
        key = key.strip()
        value = value.strip()
        if not value:
            new_dict: Dict[str, Any] = {}
            current[key] = new_dict
            stack.append((indent + 2, new_dict))
        else:
            if value.lower() in {'true', 'false'}:
                val: Any = value.lower() == 'true'
            else:
                try:
                    val = int(value)
                except ValueError:
                    try:
                        val = float(value)
                    except ValueError:
                        val = value
            current[key] = val
    return result

import json

OPT_INDENT_2 = 0

def loads(b):
    if isinstance(b, (bytes, bytearray)):
        return json.loads(b.decode("utf-8"))
    return json.loads(b)

def dumps(obj, option=0):
    return json.dumps(obj, indent=2 if option == OPT_INDENT_2 else None).encode("utf-8")

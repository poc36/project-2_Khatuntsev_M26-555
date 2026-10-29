import shlex


def parse_value(token):
    """Превращает текст в значение: "abc" -> str, true -> bool, 28 -> int"""
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    try:
        return int(token)
    except ValueError:
        raise ValueError(token) from None


def parse_values(text):
    """'("Sergei", 28, true)' -> ['Sergei', 28, True]"""
    text = text.strip()
    if not (text.startswith("(") and text.endswith(")")):
        raise ValueError(text)
    lexer = shlex.shlex(text[1:-1], posix=False)
    lexer.whitespace = ","
    lexer.whitespace_split = True
    return [parse_value(token) for token in lexer]


def parse_condition(text):
    """'age = 28' -> {'age': 28}"""
    column, sep, value = text.partition("=")
    column = column.strip()
    if not sep or not column:
        raise ValueError(text)
    return {column: parse_value(value)}
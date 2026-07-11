import html


def normalize_string(text: str) -> str:
    text = " ".join(text.split())
    return text.lower().capitalize()


def html_escape(text: str) -> str:
    return html.escape(text)

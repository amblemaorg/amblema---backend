# -*- coding: utf-8 -*-
# app/services/vademecum/header_detection.py
"""Detección del encabezado "<Tipo> <N>[A]. <Título>" y cortes propuestos (API-09).

Funciones puras (sin PDF ni BD) para probarlas con el texto real de los compendios.
Variantes vistas en las muestras: "1.  Título", "44.Título", "17 .Título", "16 Título",
"45A .Título" y el tipo en una línea y el número en la siguiente. El texto se normaliza con
NFKC (la ligadura "ﬁ" pasa a "fi") y se comparan tipos sin mayúsculas ni acentos.
"""

import re
import unicodedata

# Número de 1 a 3 cifras, "A" de continuación opcional (no la inicial de una palabra:
# "16 Aprendiendo" es la ficha 16), punto opcional y el título
NUMBER_LINE = re.compile(
    r"^(?P<number>\d{1,3})(?!\d)\s*(?:(?P<cont>[Aa])(?![^\W\d_]))?\s*\.?\s*(?P<title>.*)$",
    re.UNICODE)
MAX_NUMBER = 999


def normalize_text(text):
    """NFKC y espacios colapsados."""
    text = unicodedata.normalize("NFKC", text or u"")
    return u" ".join(text.split())


def fold(text):
    """Para comparar: sin acentos ni mayúsculas."""
    decomposed = unicodedata.normalize("NFKD", normalize_text(text))
    return u"".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _after_header_name(line, headerName):
    """Resto de la línea tras el nombre del tipo, o None si la línea no empieza por él."""
    normalized = normalize_text(line)
    folded, name = fold(normalized), fold(headerName)
    if not name or not folded.startswith(name):
        return None
    rest = folded[len(name):]
    if rest and rest[0].isalnum():
        return None  # "Ambientes" no es "Ambiente"
    # En español, quitar acentos no cambia el largo: el resto se toma del texto con acentos
    if len(folded) == len(normalized):
        rest = normalized[len(name):]
    return rest.strip(u" |-–:")


def parse_number_line(text):
    """(number, isContinuation, title) de "41A. Título", o None si no empieza por número."""
    match = NUMBER_LINE.match(normalize_text(text))
    if not match:
        return None
    number = int(match.group("number"))
    if not 1 <= number <= MAX_NUMBER:
        return None
    title = match.group("title").strip(u" .|-–:") or None
    return number, bool(match.group("cont")), title


def detect_header(lines, headerName):
    """Busca el encabezado en las primeras líneas de una página (de arriba abajo).

    Devuelve dict(headerText, number, isContinuation, title); number None si no se leyó.
    """
    lines = [normalize_text(l) for l in lines if normalize_text(l)]
    for index, line in enumerate(lines):
        rest = _after_header_name(line, headerName)
        if rest is None:
            continue
        candidates = [rest] if rest else []
        if index + 1 < len(lines):
            candidates.append(lines[index + 1])
        for candidate in candidates:
            parsed = parse_number_line(candidate)
            if parsed:
                number, isContinuation, title = parsed
                return {"headerText": u"{} {}".format(normalize_text(headerName), candidate),
                        "number": number, "isContinuation": isContinuation, "title": title}
        return {"headerText": line, "number": None, "isContinuation": False, "title": None}
    return {"headerText": None, "number": None, "isContinuation": False, "title": None}


def propose_cuts(pages):
    """Agrupa páginas consecutivas en fichas.

    `pages`: lista de dict con index, number, isContinuation, title (en orden).
    - Una página con número y sin "A" abre una ficha.
    - "NA" se une a la ficha N abierta justo antes; si no hay, abre una con ese número.
    - Una página sin encabezado queda sola y sin número: el administrador decide.
    """
    cuts = []
    current = None
    for page in pages:
        number = page.get("number")
        if number is None:
            current = None
            cuts.append({"pages": [page["index"]], "number": None, "title": None,
                         "excluded": False})
            continue
        if page.get("isContinuation") and current and current["number"] == number:
            current["pages"].append(page["index"])
            if not current["title"]:
                current["title"] = page.get("title")
            continue
        current = {"pages": [page["index"]], "number": number, "title": page.get("title"),
                   "excluded": False}
        cuts.append(current)
    return cuts

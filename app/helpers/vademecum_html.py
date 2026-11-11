# -*- coding: utf-8 -*-
# app/helpers/vademecum_html.py
"""Saneado de HTML limitado para los textos del sitio de Vademécum (API-12).

Lista blanca con la librería estándar (sin dependencias nuevas): etiquetas de formato
básico y enlaces http(s)/mailto. Se descarta todo atributo no permitido y el contenido de
script/style; el resto del texto se escapa.
"""

from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {"p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li", "a", "h2", "h3",
                "h4", "blockquote"}
VOID_TAGS = {"br"}
DROP_CONTENT = {"script", "style", "iframe", "object", "embed", "template", "noscript"}
SAFE_SCHEMES = ("http://", "https://", "mailto:")


class _Sanitizer(HTMLParser):

    def __init__(self):
        super(_Sanitizer, self).__init__(convert_charrefs=True)
        self.out = []
        self.open = []
        self.dropping = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_CONTENT:
            self.dropping += 1
            return
        if self.dropping or tag not in ALLOWED_TAGS:
            return
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if not href.strip().lower().startswith(SAFE_SCHEMES):
                self.out.append("<a>")
            else:
                self.out.append('<a href="{}" target="_blank" rel="noopener noreferrer">'
                                .format(escape(href.strip(), quote=True)))
        else:
            self.out.append("<{}>".format(tag))
        if tag not in VOID_TAGS:
            self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in self.open and tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in DROP_CONTENT:
            self.dropping = max(0, self.dropping - 1)
            return
        if self.dropping or tag not in self.open:
            return
        # Cierra lo que quedó abierto dentro (HTML mal anidado)
        while self.open:
            current = self.open.pop()
            self.out.append("</{}>".format(current))
            if current == tag:
                break

    def handle_data(self, data):
        if not self.dropping:
            self.out.append(escape(data, quote=False))

    def result(self):
        while self.open:
            self.out.append("</{}>".format(self.open.pop()))
        return "".join(self.out)


def sanitize_html(value):
    if value is None:
        return None
    parser = _Sanitizer()
    parser.feed(value)
    parser.close()
    return parser.result().strip()

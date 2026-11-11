# -*- coding: utf-8 -*-
# app/tests/unitary/vademecum_header_detection_test.py
"""Detección de encabezados y cortes propuestos (API-09), sin PDF ni BD.

Las líneas son el texto real extraído con PyMuPDF de los compendios de muestra
(Vademecum/PDFs, fuera del repo). La prueba con los PDF completos está en
app/tests/integration/vademecum_compendium_samples_test.py y corre si se define
VADEMECUM_SAMPLES_DIR.
"""

import unittest

from app.services.vademecum.header_detection import (
    detect_header, normalize_text, parse_number_line, propose_cuts)

# (tipo, líneas superiores de la página, número, continuación, título esperado)
REAL_HEADERS = [
    (u"Ingenio Matemático", [u"Ingenio Matemático", u"1.  Problemas de conteo geométrico"],
     1, False, u"Problemas de conteo geométrico"),
    (u"Ingenio Matemático", [u"Ingenio Matemático", u"1A.  Problemas de conteo geométrico"],
     1, True, u"Problemas de conteo geométrico"),
    (u"Ingenio Matemático", [u"Ingenio Matemático", u"10A. Problemas de balanza"],
     10, True, u"Problemas de balanza"),
    (u"Momento X", [u"Momento X", u"16 Aprendiendo a Multiplicar con el Método Japonés  "],
     16, False, u"Aprendiendo a Multiplicar con el Método Japonés"),
    (u"Momento X", [u"Momento X", u"17 .Aprendiendo a Multiplicar"],
     17, False, u"Aprendiendo a Multiplicar"),
    (u"Momento X", [u"Momento X 15A. Conjunto de corazones"],
     15, True, u"Conjunto de corazones"),
    (u"Momento X", [u"Momento X", u"38.Múltiplos con Regletas de Cuisenaire"],
     38, False, u"Múltiplos con Regletas de Cuisenaire"),
    (u"Momento X", [u"Momento X", u"23. ¡Multiplica y Gana!"], 23, False, u"¡Multiplica y Gana!"),
    (u"Hora TAL", [u"Hora TAL", u"44.Lectura y Representación de Escenas  "],
     44, False, u"Lectura y Representación de Escenas"),
    (u"Hora TAL", [u"Hora TAL", u"45A .Identificación y Uso del Acento Ortográfico"],
     45, True, u"Identificación y Uso del Acento Ortográfico"),
    (u"Hora TAL", [u"Hora TAL", u"41. Identifica la Palabra Incongruente"],
     41, False, u"Identifica la Palabra Incongruente"),
    (u"Ambiente", [u"Ambiente 1. Venezuela megadiversa"], 1, False, u"Venezuela megadiversa"),
]


class HeaderDetectionTest(unittest.TestCase):

    def test_real_headers_from_the_samples(self):
        for headerName, lines, number, isContinuation, title in REAL_HEADERS:
            header = detect_header(lines, headerName)
            self.assertEqual((header["number"], header["isContinuation"], header["title"]),
                             (number, isContinuation, title), lines)
            self.assertTrue(header["headerText"].startswith(headerName), header)

    def test_fi_ligature_is_normalized_with_nfkc(self):
        header = detect_header([u"Hora TAL", u"12. Identiﬁca la palabra"], u"Hora TAL")
        self.assertEqual(header["title"], u"Identifica la palabra")
        self.assertEqual(normalize_text(u"ﬁcha  de prueba"), u"ficha de prueba")

    def test_type_name_ignores_case_and_accents_but_not_longer_words(self):
        self.assertEqual(detect_header([u"INGENIO MATEMATICO", u"3. Conteo"],
                                       u"Ingenio Matemático")["number"], 3)
        self.assertIsNone(detect_header([u"Ambientes naturales", u"3. Ríos"],
                                        u"Ambiente")["number"])

    def test_page_without_numbered_header(self):
        # Ambiente todavía sin el encabezado común (AMB-01)
        header = detect_header([u"Venezuela Megadiversa", u"Ambiente"], u"Ambiente")
        self.assertEqual((header["number"], header["headerText"]), (None, u"Ambiente"))
        header = detect_header([u"Regiones de Venezuela"], u"Ambiente")
        self.assertEqual(header, {"headerText": None, "number": None,
                                  "isContinuation": False, "title": None})

    def test_other_type_header_is_not_read_as_this_type(self):
        self.assertIsNone(detect_header([u"Hora TAL", u"41. Título"], u"Momento X")["number"])

    def test_number_line_variants(self):
        self.assertEqual(parse_number_line(u"7A"), (7, True, None))
        self.assertEqual(parse_number_line(u"3a. Título"), (3, True, u"Título"))
        self.assertIsNone(parse_number_line(u"Título 3"))
        self.assertIsNone(parse_number_line(u"0. Portada"))
        self.assertIsNone(parse_number_line(u"1234. Año"))


class ProposeCutsTest(unittest.TestCase):

    def page(self, index, number=None, cont=False, title=None):
        return {"index": index, "number": number, "isContinuation": cont, "title": title}

    def test_na_joins_the_previous_sheet(self):
        cuts = propose_cuts([self.page(0, 1, title=u"Uno"), self.page(1, 1, True, u"Uno"),
                             self.page(2, 2, title=u"Dos"), self.page(3, 3, title=u"Tres"),
                             self.page(4, 3, True)])
        self.assertEqual([(c["pages"], c["number"], c["title"]) for c in cuts],
                         [([0, 1], 1, u"Uno"), ([2], 2, u"Dos"), ([3, 4], 3, u"Tres")])
        self.assertFalse(any(c["excluded"] for c in cuts))

    def test_continuation_of_another_number_opens_a_sheet(self):
        cuts = propose_cuts([self.page(0, 1), self.page(1, 2, True, u"Dos")])
        self.assertEqual([(c["pages"], c["number"]) for c in cuts], [([0], 1), ([1], 2)])

    def test_pages_without_header_stay_alone_for_review(self):
        cuts = propose_cuts([self.page(0, 1), self.page(1), self.page(2, 1, True)])
        self.assertEqual([(c["pages"], c["number"]) for c in cuts],
                         [([0], 1), ([1], None), ([2], 1)])

    def test_real_sequence_momento_x_part_b(self):
        sequence = [(15, False), (15, True), (16, False), (16, True), (17, False), (18, False),
                    (19, False), (20, False), (21, False), (22, False), (23, False),
                    (24, False), (25, False), (26, False), (27, False), (28, False),
                    (29, False), (29, True), (30, False), (31, False)]
        cuts = propose_cuts([self.page(i, n, c) for i, (n, c) in enumerate(sequence)])
        self.assertEqual([c["number"] for c in cuts], list(range(15, 32)))
        self.assertEqual(cuts[0]["pages"], [0, 1])
        self.assertEqual(cuts[14]["pages"], [16, 17])  # 29 y 29A


if __name__ == "__main__":
    unittest.main()

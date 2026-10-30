# app/tests/unitary/model_defaults_test.py

import importlib
import pkgutil
import unittest

from mongoengine.base import BaseDocument, get_document
from mongoengine.base.common import _document_registry

import app.models
import app.blueprints.web_content.models


def _load_models():
    for package in (app.models, app.blueprints.web_content.models):
        for module in pkgutil.iter_modules(package.__path__):
            importlib.import_module('{}.{}'.format(package.__name__, module.name))


class ModelDefaultsTest(unittest.TestCase):
    """
    Un default que es una instancia (default=Clase()) se comparte entre todos los documentos
    del proceso: modificarlo en uno lo modifica en los demás. Debe ser invocable (default=Clase).
    """

    def test_no_shared_embedded_instances_as_default(self):
        _load_models()
        # Si el registro viniera vacio la prueba pasaria sin revisar nada
        self.assertGreater(len(_document_registry), 50)
        shared = []
        for name in list(_document_registry):
            document = get_document(name)
            for fieldName, field in document._fields.items():
                if isinstance(field.default, BaseDocument):
                    shared.append('{}.{}'.format(name, fieldName))
        self.assertEqual(shared, [])

    def test_new_documents_get_their_own_instances(self):
        from app.models.school_year_model import SchoolYear
        from app.models.peca_project_model import PecaProject
        self.assertIsNot(SchoolYear().olympicsSummary, SchoolYear().olympicsSummary)
        self.assertIsNot(PecaProject().yearbook, PecaProject().yearbook)
        self.assertIsNot(PecaProject().yearbook.lapse1, PecaProject().yearbook.lapse1)


if __name__ == "__main__":
    unittest.main()

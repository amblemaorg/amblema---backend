# app/tests/integration/web_content_about_test.py


import unittest
import json

from flask import current_app

from app import create_app
from app.tests.base import drop_testing_database
from app.blueprints.web_content.models.web_content import WebContent
from app.blueprints.web_content.models.about_us_page_model import (
    AULA_ACTIVA_GALLERY_MAX)


IMAGE = '/resources/images/webcontent/aula-activa-{}.jpg'


def about_payload(gallery=None):
    page = {
        "slider": [{"image": IMAGE.format('slider'), "description": "Slider"}],
        "aboutUsText": "Sobre AmbLeMa",
        "environmentText": "Ambiente",
        "readingText": "Lectura",
        "mathText": "Matemática",
        "aulaActivaText": "Aula Activa",
        "awards": [{
            "title": "Premio",
            "image": IMAGE.format('award1'),
            "image2": IMAGE.format('award2'),
            "image3": IMAGE.format('award3'),
            "description": "Premio AmbLeMa"}],
    }
    if gallery is not None:
        page["aulaActivaGallery"] = gallery
    return {"aboutUsPage": page}


class WebContentAboutTest(unittest.TestCase):
    """Página Nosotros: galería de fotos de Aula Activa AmbLeMa."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.app.app_context().push()
        from app import db
        self.db = db
        self.client = self.app.test_client

    def tearDown(self):
        drop_testing_database(self.db)

    def json(self, res):
        return json.loads(res.data)

    def about(self):
        res = self.client().get('/webcontent?page=aboutUsPage')
        self.assertEqual(res.status_code, 200)
        return self.json(res)['aboutUsPage']

    def save(self, payload):
        return self.client().post(
            '/webcontent?page=aboutUsPage',
            data=json.dumps(payload),
            content_type='application/json')

    def test_existing_document_without_gallery_returns_empty_list(self):
        page = about_payload()['aboutUsPage']
        WebContent._get_collection().insert_one({"aboutUsPage": page})

        about = self.about()
        self.assertEqual(about['aulaActivaGallery'], [])
        self.assertEqual(about['aulaActivaText'], "Aula Activa")

    def test_save_gallery_with_optional_description(self):
        gallery = [
            {"image": IMAGE.format(1), "description": "Siembra en el patio"},
            {"image": IMAGE.format(2), "description": ""},
            {"image": IMAGE.format(3)},
        ]
        res = self.save(about_payload(gallery))
        self.assertEqual(res.status_code, 201)

        serverUrl = current_app.config.get('SERVER_URL') or ''
        saved = self.about()['aulaActivaGallery']
        self.assertEqual([g['image'] for g in saved],
                         [serverUrl + IMAGE.format(i) for i in (1, 2, 3)])
        self.assertEqual(saved[0]['description'], "Siembra en el patio")
        self.assertEqual(saved[1]['description'], "")
        self.assertIsNone(saved[2]['description'])

    def test_gallery_image_with_server_url_is_stored_as_relative_path(self):
        serverUrl = current_app.config.get('SERVER_URL')
        if not serverUrl:
            self.skipTest('SERVER_URL no configurado')
        res = self.save(about_payload(
            [{"image": serverUrl + IMAGE.format(1), "description": ""}]))
        self.assertEqual(res.status_code, 201)

        stored = WebContent.objects().first().aboutUsPage.aulaActivaGallery
        self.assertEqual(stored[0].image, IMAGE.format(1))

    def test_gallery_rejects_more_than_max_images(self):
        gallery = [{"image": IMAGE.format(i), "description": ""}
                   for i in range(AULA_ACTIVA_GALLERY_MAX + 1)]
        res = self.save(about_payload(gallery))
        self.assertEqual(res.status_code, 400)
        self.assertIn('aulaActivaGallery', self.json(res)['aboutUsPage'])
        self.assertIsNone(WebContent.objects().first())

    def test_gallery_rejects_long_description(self):
        res = self.save(about_payload(
            [{"image": IMAGE.format(1), "description": "x" * 55}]))
        self.assertEqual(res.status_code, 400)

    def test_saving_without_gallery_clears_it(self):
        """El backoffice siempre envía la página completa: omitir la galería la vacía."""
        self.assertEqual(self.save(about_payload(
            [{"image": IMAGE.format(1), "description": ""}])).status_code, 201)
        self.assertEqual(self.save(about_payload()).status_code, 201)
        self.assertEqual(self.about()['aulaActivaGallery'], [])


if __name__ == '__main__':
    unittest.main()

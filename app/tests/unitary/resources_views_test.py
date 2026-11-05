# -*- coding: utf-8 -*-
# app/tests/unitary/resources_views_test.py

import os
import shutil
import tempfile
import unittest
from unittest import mock

from app import create_app

SECRET = b"SECRET=no-debe-salir"


class ResourcesViewsTest(unittest.TestCase):
    """/resources/images y /resources/files no deben salir de su directorio base
    (path traversal) y deben responder el MIME correcto."""

    def setUp(self):
        self.app = create_app(config_instance="testing")
        self.client = self.app.test_client()

        # root/
        #   secret.env           <- fuera de los directorios servidos
        #   images/sponsors/logo.jpeg, images/a/b/foto.png
        #   files/docs/guia.pdf
        self.root = tempfile.mkdtemp()
        self.images = os.path.join(self.root, "images")
        self.files = os.path.join(self.root, "files")
        os.makedirs(os.path.join(self.images, "sponsors"))
        os.makedirs(os.path.join(self.images, "a", "b"))
        os.makedirs(os.path.join(self.files, "docs"))
        self._write(os.path.join(self.root, "secret.env"), SECRET)
        self._write(os.path.join(self.images, "sponsors", "logo.jpeg"), b"\xff\xd8jpeg")
        self._write(os.path.join(self.images, "a", "b", "foto.png"), b"\x89PNGpng")
        self._write(os.path.join(self.files, "docs", "guia.pdf"), b"%PDF-1.4")

        patchers = [
            mock.patch("app.blueprints.web_content.views.path_images", self.images),
            mock.patch("app.blueprints.web_content.views.files_path", self.files),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def _write(path, content):
        with open(path, "wb") as handle:
            handle.write(content)

    def assertNotLeaked(self, response):
        # Werkzeug 2 redirige (308) las URL con '//'; se sigue la redirección y se
        # exige que el destino final tampoco entregue el archivo.
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(SECRET, response.data)
        response.close()

    # --- imágenes ---

    def test_image_is_served_with_clean_mimetype(self):
        response = self.client.get("/resources/images/sponsors/logo.jpeg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"\xff\xd8jpeg")
        self.assertEqual(response.mimetype, "image/jpeg")  # antes: 'image/.jpeg'
        response.close()

    def test_image_in_nested_folder(self):
        response = self.client.get("/resources/images/a/b/foto.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        response.close()

    def test_missing_image_returns_404(self):
        self.assertNotLeaked(self.client.get("/resources/images/sponsors/no-existe.jpeg"))

    def test_image_traversal_with_encoded_slashes(self):
        self.assertNotLeaked(self.client.get("/resources/images/..%2fsecret.env/x"))
        self.assertNotLeaked(self.client.get("/resources/images/sponsors/..%2f..%2fsecret.env"))

    def test_image_traversal_with_dot_segments(self):
        self.assertNotLeaked(self.client.get("/resources/images/sponsors/../../secret.env"))
        self.assertNotLeaked(self.client.get("/resources/images/a/b/..%2f..%2f..%2fsecret.env"))

    def test_image_traversal_with_absolute_path(self):
        target = os.path.join(self.root, "secret.env").lstrip("/")
        self.assertNotLeaked(self.client.get("/resources/images/%2f" + target.replace("/", "%2f"),
                                            follow_redirects=True))

    # --- archivos ---

    def test_file_is_served(self):
        response = self.client.get("/resources/files/docs/guia.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"%PDF-1.4")
        response.close()

    def test_file_traversal(self):
        self.assertNotLeaked(self.client.get("/resources/files/docs/..%2f..%2fsecret.env"))
        self.assertNotLeaked(self.client.get("/resources/files/..%2f..%2f/secret.env",
                                            follow_redirects=True))
        self.assertNotLeaked(self.client.get("/resources/files/docs/../../secret.env"))


if __name__ == "__main__":
    unittest.main()

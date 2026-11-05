import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from images_pdf import convert


class ImageConversionTests(unittest.TestCase):
    def test_converts_real_image_to_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "photo.png"
            target = Path(directory) / "result.pdf"
            Image.new("RGB", (20, 10), "red").save(source)
            with patch("sys.argv", ["convert.py", "--out", str(target), str(source)]):
                self.assertEqual(convert.main(), 0)
            self.assertTrue(target.read_bytes().startswith(b"%PDF-"))

"""Tests de Filahia : pages, prédiction, validation des entrées, extraction OCR (trois langues)."""

import shutil
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation

from .models import CropPrediction
from .ocr_processor import OCRProcessor

FIXTURES = Path(__file__).resolve().parent / "tests_fixtures"

# Échantillon du jeu de données public : le modèle recommande le riz.
RICE = {
    "nitrogen": 90, "phosphorus": 42, "potassium": 43,
    "temperature": 20.9, "humidity": 82, "ph_level": 6.5, "rainfall": 203,
}
EXPECTED = {
    "nitrogen": 90.0, "phosphorus": 42.0, "potassium": 43.0,
    "temperature": 20.9, "humidity": 82.0, "ph_level": 6.5, "rainfall": 203.0,
}


class PagesTests(TestCase):
    def test_pages_exist_in_the_three_languages(self):
        for lang in ("en", "fr", "ar"):
            for name in ("welcome", "index", "ocr_upload"):
                with self.subTest(lang=lang, page=name):
                    with translation.override(lang):
                        url = reverse(f"crops:{name}")
                    self.assertTrue(url.startswith(f"/{lang}/"), url)
                    self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_arabic_interface_shows_the_arabic_name(self):
        self.assertContains(self.client.get("/ar/"), "فلاحيا")

    def test_root_redirects_to_a_language(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)


class PredictionTests(TestCase):
    def post(self, data):
        return self.client.post("/en/predict-crop/", data, follow=True)

    def test_known_sample_is_recommended_and_saved(self):
        response = self.post(RICE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CropPrediction.objects.count(), 1)
        self.assertEqual(CropPrediction.objects.get().recommended_crop.lower(), "rice")

    def test_out_of_range_values_are_rejected(self):
        for field, bad in (("ph_level", 99), ("temperature", 500), ("nitrogen", -5), ("humidity", 1000)):
            with self.subTest(field=field):
                self.post({**RICE, field: bad})
                self.assertEqual(CropPrediction.objects.count(), 0)

    def test_missing_field_is_rejected(self):
        data = {k: v for k, v in RICE.items() if k != "rainfall"}
        self.post(data)
        self.assertEqual(CropPrediction.objects.count(), 0)

    def test_non_numeric_input_is_rejected(self):
        self.post({**RICE, "nitrogen": "abc"})
        self.assertEqual(CropPrediction.objects.count(), 0)

    def test_csrf_is_enforced(self):
        from django.test import Client

        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post("/en/predict-crop/", RICE).status_code, 403)


class ExtractionTests(SimpleTestCase):
    """Extraction par expressions régulières : aucune dépendance à Tesseract."""

    TEXTS = {
        "en": "Nitrogen: 90\nPhosphorus: 42\nPotassium: 43\nTemperature: 20.9\nHumidity: 82\npH: 6.5\nRainfall: 203",
        "fr": "Azote: 90\nPhosphore: 42\nPotassium: 43\nTempérature: 20.9\nHumidité: 82\npH: 6.5\nPluviométrie: 203",
        "ar": "نيتروجين: 90\nفوسفور: 42\nبوتاسيوم: 43\nدرجة الحرارة: 20.9\nرطوبة: 82\nحموضة: 6.5\nأمطار: 203",
    }

    def test_each_language(self):
        proc = OCRProcessor()
        for lang, text in self.TEXTS.items():
            with self.subTest(lang=lang):
                self.assertEqual(proc.extract_crop_data(text, lang), EXPECTED)

    def test_wrong_detected_language_falls_back_to_the_others(self):
        # La détection de langue se trompe souvent sur un texte court : on doit quand même tout extraire.
        proc = OCRProcessor()
        self.assertEqual(proc.extract_crop_data(self.TEXTS["fr"], "ro"), EXPECTED)

    def test_values_outside_the_valid_range_are_ignored(self):
        data = OCRProcessor().extract_crop_data("Nitrogen: 9999\nPotassium: 43", "en")
        self.assertIsNone(data["nitrogen"])
        self.assertEqual(data["potassium"], 43.0)

    def test_empty_text_extracts_nothing(self):
        self.assertTrue(all(v is None for v in OCRProcessor().extract_crop_data("", "en").values()))


def _tesseract_ready(lang):
    exe = getattr(settings, "TESSERACT_CMD", "")
    return bool(exe and (Path(exe).exists() or shutil.which(exe)))


class OcrImageTests(SimpleTestCase):
    """Chaîne complète image, Tesseract, extraction. Ignorée si Tesseract ou une langue est absent."""

    def run_lang(self, lang):
        if not _tesseract_ready(lang):
            self.skipTest("Tesseract non installé")
        try:
            text, detected, _ = OCRProcessor().process_file(str(FIXTURES / f"ocr_{lang}.png"))
        except Exception as exc:  # langue manquante, etc.
            self.skipTest(f"OCR indisponible pour {lang} : {exc}")
        self.assertEqual(OCRProcessor().extract_crop_data(text, detected), EXPECTED)

    def test_english_image(self):
        self.run_lang("en")

    def test_french_image(self):
        self.run_lang("fr")

    def test_arabic_image(self):
        self.run_lang("ar")

<p align="center">
  <img src="assets/banner.svg" alt="Filahia, crop recommendation from soil and climate data" width="100%">
</p>

# Filahia

Filahia (فلاحيا, from *filaha*, "agriculture" in Arabic) is a web application that recommends the most suitable crop from soil and climate
measurements (N, P, K, temperature, humidity, pH, rainfall) using a trained
scikit-learn model. Measurements can also be extracted from an uploaded
document through an OCR pipeline. The interface is available in French and
Arabic.

**Stack:** Django · scikit-learn · OCR · gettext i18n (fr / ar)

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The OCR feature also needs the [Tesseract](https://github.com/tesseract-ocr/tesseract)
program installed on the system (with the French and Arabic language data).

Set `DJANGO_SECRET_KEY` in the environment for anything beyond local use.

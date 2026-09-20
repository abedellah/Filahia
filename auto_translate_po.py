import polib
from googletrans import Translator
import time
#pip install django pytesseract opencv-python numpy pillow PyMuPDF langdetect

# Chemin vers ton fichier .po
po_path = 'locale/fr/LC_MESSAGES/django.po'

# Charge le fichier .po
po = polib.pofile(po_path)

# Initialise le traducteur
translator = Translator()

for entry in po:
    if not entry.msgstr.strip():  # Si msgstr vide
        try:
            translation = translator.translate(entry.msgid, dest='fr').text
            entry.msgstr = translation
            print(f'Traduit: "{entry.msgid}" -> "{translation}"')
            time.sleep(1)  # Pause pour éviter les blocages API
        except Exception as e:
            print(f"Erreur sur '{entry.msgid}': {e}")

# Enregistre les traductions dans le fichier
po.save()
print("Traductions terminées et sauvegardées.")

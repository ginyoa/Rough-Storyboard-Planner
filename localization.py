import json
from pathlib import Path

# How to add new languages:
# 1. Create a new JSON file in the locales directory with the language code (e.g., "es.json" for Spanish).
# 2. Use the same keys as in the existing language files.
# 3. Translate the values to the new language.
# 4. In the main file, add the new language to the languages list and the corresponding name to the lists "languages_code" and "languages" (use the search function to find the lists). Example: "es" for the code and "Español" for the name.

class Localization:
    def __init__(self, lang="en"):
        self.lang = lang
        self.strings = {}
        self.load_language(lang)

    def load_language(self, lang):
        path = Path(f"locales/{lang}.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.strings = json.load(f)
            print("loaded:", lang)
        else:
            self.strings = {}

    def tr(self, key, **kwargs):
        text = self.strings.get(key)
        if text is None:
            text = f"missing:{key}"
        return text.format(**kwargs)
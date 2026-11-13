from pathlib import Path
import json
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
content_file = root / "app/src/main/assets/content.json"
pack = json.loads(content_file.read_text(encoding="utf-8"))
for name in ("readings", "words", "facts"):
    items = pack.get(name)
    assert isinstance(items, list) and items, f"{name}: content missing"
    ids = [item.get("id") for item in items]
    assert all(isinstance(i, str) and 1 <= len(i) <= 100 for i in ids), f"{name}: bad ID"
    assert len(ids) == len(set(ids)), f"{name}: duplicate IDs"
    assert all(isinstance(item.get("category"), str) and item["category"].strip()
               for item in items), f"{name}: blank category"

known_words = {word["id"] for word in pack["words"]}
for item in pack["readings"]:
    assert len(item.get("title", "").strip()) > 5, f"Missing title: {item['id']}"
    assert len(item.get("paragraphs", [])) >= 2, f"Missing paragraphs: {item['id']}"
    assert all(isinstance(p, str) and p.strip() for p in item["paragraphs"]), item["id"]
    choices = item.get("options", [])
    assert isinstance(choices, list) and len(choices) == 4, f"Need 4 choices: {item['id']}"
    assert len(set(choices)) == 4, f"Duplicate choices: {item['id']}"
    assert type(item.get("answer")) is int and 0 <= item["answer"] < 4, f"Wrong answer index: {item['id']}"
    assert set(item.get("wordIds", [])) <= known_words, f"Missing linked word: {item['id']}"

for word in pack["words"]:
    for field in ("word", "meaning", "example"):
        assert isinstance(word.get(field), str) and len(word[field].strip()) > 2, f"Bad {field}: {word['id']}"

for fact in pack["facts"]:
    for field in ("title", "body"):
        assert isinstance(fact.get(field), str) and len(fact[field].strip()) >= 5, f"Bad {field}: {fact['id']}"

manifest = (root / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
assert 'android:allowBackup="false"' in manifest, "Auto backup must be explicitly disabled"
assert 'android:usesCleartextTraffic="false"' in manifest, "Only encrypted network connections allowed"

backup = (root / "app/src/main/java/com/merak/app/MerakBackup.kt").read_text(encoding="utf-8")
assert "fun restore(context: Context, text: String): Int" in backup
assert "MAX_BYTES" in backup and 'context.getSharedPreferences(PREFS' in backup

print("Quality checks passed:",
      len(pack["readings"]), "readings;",
      len(pack["words"]), "words;",
      len(pack["facts"]), "facts.")

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    raise SystemExit("Usage: security_verify.py <android-project-dir> <aapt-permissions-file>")
root = Path(sys.argv[1])
perm_file = Path(sys.argv[2])
ns = "{http://schemas.android.com/apk/res/android}"

manifest = ET.parse(root / "app/src/main/AndroidManifest.xml").getroot()
application = manifest.find("application")
if application is None:
    raise SystemExit("Application node is missing")
declared = {p.get(ns + "name") for p in manifest.findall("uses-permission")}
expected_declared = {
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE"
}
if declared != expected_declared:
    raise SystemExit(f"Unexpected permissions in app manifest: {declared ^ expected_declared}")
if application.get(ns + "allowBackup") != "false":
    raise SystemExit("App data backup must be explicitly disabled until safe backups are implemented.")
if application.get(ns + "usesCleartextTraffic") != "false":
    raise SystemExit("Cleartext HTTP traffic must be disabled.")
for component in application:
    name = component.get(ns + "name", "")
    if component.get(ns + "exported") == "true" and name != ".MainActivity":
        raise SystemExit(f"Unexpected exported component: {name}")

permissions_text = perm_file.read_text(encoding="utf-8", errors="replace")
apks = set(re.findall(r"uses-permission:\s+name='([^']+)'", permissions_text))
dangerous = {
    "android.permission.CAMERA", "android.permission.RECORD_AUDIO",
    "android.permission.READ_CONTACTS", "android.permission.WRITE_CONTACTS",
    "android.permission.READ_SMS", "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS", "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION", "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.MANAGE_EXTERNAL_STORAGE", "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO", "android.permission.READ_MEDIA_AUDIO",
    "android.permission.QUERY_ALL_PACKAGES", "android.permission.POST_NOTIFICATIONS"
}
if apks & dangerous:
    raise SystemExit(f"Unexpected sensitive APK permissions: {sorted(apks & dangerous)}")
if not expected_declared.issubset(apks):
    raise SystemExit(f"APK missing expected permissions: {expected_declared - apks}")

main = (root / "app/src/main/java/com/merak/app/MainActivity.kt").read_text(encoding="utf-8")
data = (root / "app/src/main/java/com/merak/app/MerakData.kt").read_text(encoding="utf-8")
assert 'safeUri.host != "tr.wikipedia.org"' in main, "External URL whitelist missing"
assert 'connection.instanceFollowRedirects = false' in data, "Redirect policy missing"
assert 'if (output.length + count > 524288)' in data, "Network response size cap missing"
assert 'https://tr.wikipedia.org/w/api.php' in data, "Expected data provider changed"

print("Security checks passed.")
print("APK permissions:", ", ".join(sorted(apks)))
print("NOTICE: APK is a debug beta, not a production-signed release.")
print("NOTICE: Backups are disabled; uninstalling may erase personal notes.")

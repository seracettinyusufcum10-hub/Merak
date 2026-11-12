from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
manifest = root / "app/src/main/AndroidManifest.xml"
main = root / "app/src/main/java/com/merak/app/MainActivity.kt"
data = root / "app/src/main/java/com/merak/app/MerakData.kt"

def replace_once(text, old, new, name):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{name}: expected exactly one occurrence, found {n}")
    return text.replace(old, new, 1)

m = manifest.read_text(encoding="utf-8")
m = replace_once(m,
    'android:allowBackup="false"',
    'android:allowBackup="false"\n        android:usesCleartextTraffic="false"',
    "No unencrypted HTTP in manifest")
manifest.write_text(m, encoding="utf-8")

ui = main.read_text(encoding="utf-8")
ui = replace_once(ui,
    '''    fun openUrl(url: String) {
        runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }
    }''',
    '''    fun openUrl(url: String) {
        // The online discovery provider is Wikipedia. Never open an arbitrary link.
        val safeUri = runCatching { Uri.parse(url) }.getOrNull() ?: return
        if (safeUri.scheme != "https" ||
            safeUri.host != "tr.wikipedia.org" ||
            !safeUri.userInfo.isNullOrBlank()
        ) return
        runCatching {
            context.startActivity(
                Intent(Intent.ACTION_VIEW, safeUri)
                    .addCategory(Intent.CATEGORY_BROWSABLE)
            )
        }
    }''',
    "External URL allowlist")
main.write_text(ui, encoding="utf-8")

d = data.read_text(encoding="utf-8")
d = replace_once(d,
    '''        connection.requestMethod = "GET"
        connection.connectTimeout = 9000''',
    '''        connection.requestMethod = "GET"
        connection.instanceFollowRedirects = false
        connection.useCaches = false
        connection.connectTimeout = 9000''',
    "No HTTP redirects")
d = replace_once(d,
    '''            val payload = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            val root = JSONObject(payload).optJSONObject("query") ?: return emptyList()''',
    '''            // Keep unexpectedly large responses from exhausting the device's memory.
            if (connection.contentLengthLong > 524288L) return emptyList()
            val payload = connection.inputStream.bufferedReader(Charsets.UTF_8).use { reader ->
                val output = StringBuilder()
                val chunk = CharArray(4096)
                while (true) {
                    val count = reader.read(chunk)
                    if (count < 0) break
                    if (output.length + count > 524288) return emptyList()
                    output.append(chunk, 0, count)
                }
                output.toString()
            }
            val root = JSONObject(payload).optJSONObject("query") ?: return emptyList()''',
    "Bound external JSON response")
data.write_text(d, encoding="utf-8")
print("Security hardening complete: cleartext disabled; links allowlisted; network payloads bounded.")

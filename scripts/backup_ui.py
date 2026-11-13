from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
activity = root / "app/src/main/java/com/merak/app/MainActivity.kt"
build = root / "app/build.gradle.kts"
src = activity.read_text(encoding="utf-8")

def once(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected 1 source occurrence, got {n}")
    src = src.replace(old, new, 1)

once(
    "import androidx.activity.compose.BackHandler",
    "import androidx.activity.compose.BackHandler\n"
    "import androidx.activity.compose.rememberLauncherForActivityResult\n"
    "import androidx.activity.result.contract.ActivityResultContracts",
    "Backup UI imports"
)

once(
    """private fun ProfilePage(store: MerakStore, onChange: () -> Unit, onPersonalize: () -> Unit) {
    var note by rememberSaveable { mutableStateOf(store.nightNote) }
    var chosenTopics by remember { mutableStateOf(store.interests) }
    var authorsText by rememberSaveable { mutableStateOf(store.favoriteAuthors) }
    var preferencesSaved by remember { mutableStateOf(false) }""",
    """private fun ProfilePage(store: MerakStore, onChange: () -> Unit, onPersonalize: () -> Unit) {
    val context = LocalContext.current
    var note by rememberSaveable { mutableStateOf(store.nightNote) }
    var chosenTopics by remember { mutableStateOf(store.interests) }
    var authorsText by rememberSaveable { mutableStateOf(store.favoriteAuthors) }
    var preferencesSaved by remember { mutableStateOf(false) }
    var backupStatus by rememberSaveable { mutableStateOf("") }
    var awaitingRestore by remember { mutableStateOf<String?>(null) }

    val createBackup = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) {
            backupStatus = runCatching {
                MerakBackup.write(context, uri)
                "Yedek kaydedildi. Bu dosya şifreli değil; güvenli bir yerde sakla."
            }.getOrElse { "Yedek kaydedilemedi. Lütfen başka bir konum dene." }
        }
    }
    val importBackup = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            backupStatus = runCatching {
                awaitingRestore = MerakBackup.read(context, uri)
                "Yedek doğrulandı. Onay verirsen mevcut veriler silinmeden eklenecek."
            }.getOrElse {
                awaitingRestore = null
                "Dosya geçerli bir MERAK yedeği değil veya okunamıyor."
            }
        }
    }
    if (awaitingRestore != null) {
        AlertDialog(
            onDismissRequest = { awaitingRestore = null },
            title = { Text("Yedeği geri yükle") },
            text = { Text(
                MerakBackup.inspect(awaitingRestore!!) +
                "\\nMevcut notlar silinmez. İlerleme ve tercihler eksikse yedekten eklenir."
            ) },
            confirmButton = {
                TextButton(onClick = {
                    val backupText = awaitingRestore!!
                    awaitingRestore = null
                    backupStatus = runCatching {
                        val changed = MerakBackup.restore(context, backupText)
                        note = store.nightNote
                        chosenTopics = store.interests
                        authorsText = store.favoriteAuthors
                        onPersonalize()
                        "$changed kayıt eklendi veya birleştirildi."
                    }.getOrElse { "Yedek geri yüklenemedi." }
                }) { Text("Geri yükle") }
            },
            dismissButton = {
                TextButton(onClick = { awaitingRestore = null }) { Text("Vazgeç") }
            }
        )
    }""",
    "Backup state and file-picker UI"
)
# Insert a separate card just before the existing footer:
once(
    """        SurfaceCard {
            Eyebrow("MERAK ilk sürüm")""",
    """        SurfaceCard {
            Eyebrow("VERİLERİN SENİN KONTROLÜNDE")
            Text("Notlarını ve ilerlemeni yedekle", color = Cream,
                fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            Text(
                "Uygulamayı silersen verilerin kaybolabilir. Yedeği telefonunda seçtiğin konuma kaydedebilir ve daha sonra geri yükleyebilirsin.",
                color = Muted, fontSize = 12.sp, lineHeight = 19.sp
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedSmall("Yedek oluştur", onClick = {
                    createBackup.launch("MERAK-yedek-" + dayKey() + ".json")
                })
                OutlinedSmall("Yedeği aç", onClick = {
                    importBackup.launch(arrayOf("application/json", "text/plain", "application/octet-stream"))
                })
            }
            Text("Yedek şifreli değildir. Başkalarıyla paylaşma.",
                color = Gold, fontSize = 11.sp)
            if (backupStatus.isNotBlank()) {
                Text(backupStatus, color = Muted, fontSize = 12.sp, lineHeight = 18.sp)
            }
        }
        SurfaceCard {
            Eyebrow("MERAK ilk sürüm")""",
    "Backup options card"
)
once(
    """            Text("Ruh hâlin, notların ve öğrenme geçmişin yalnızca bu cihazda saklanır. İnternete yalnızca yeni Vikipedi içerikleri almak için bağlanır.",
                color = Muted, fontSize = 12.sp, lineHeight = 20.sp)""",
    """            Text("Notların, ruh hâlin ve öğrenme geçmişin telefonunda saklanır. Aradığın konular ve seçtiğin yazar adları, çevrim içi içerik alınırken Vikipedi'ye arama sorgusu olarak gönderilebilir.",
                color = Muted, fontSize = 12.sp, lineHeight = 20.sp)""",
    "Clearer privacy disclosure"
)

# Bound accidental input that may otherwise become huge in memory or preferences.
once(
    'OutlinedTextField(value = note, onValueChange = { note = it },',
    'OutlinedTextField(value = note, onValueChange = { note = it.take(5000) },',
    "Local notes size cap"
)
activity.write_text(src, encoding="utf-8")
config = build.read_text(encoding="utf-8")
if 'versionCode = 4' not in config or 'versionName = "0.1.3"' not in config:
    raise RuntimeError("Unexpected build version; stop instead of guessing.")
config = config.replace('versionCode = 4', 'versionCode = 5', 1)
config = config.replace('versionName = "0.1.3"', 'versionName = "0.1.4"', 1)
build.write_text(config, encoding="utf-8")
print("MERAK v0.1.4: user-controlled backup, safe restore and privacy explanation enabled.")

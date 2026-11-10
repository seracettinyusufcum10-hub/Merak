from pathlib import Path
from PIL import Image
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
res = root / "app/src/main/res"
original = res / "drawable-nodpi/merak_cover.jpg"
if not original.exists():
    raise SystemExit(f"MERAK cover not found: {original}")
with Image.open(original) as im:
    cover = im.convert("RGB")
    width, height = cover.size
    banner = cover.crop((0, int(height * 0.065), width, int(height * 0.395)))
    banner.save(res / "drawable-nodpi/merak_hero.jpg", "JPEG", quality=92, optimize=True)
    side = int(width * 0.43)
    center_x = int(width * 0.495)
    top = int(height * 0.055)
    avatar = cover.crop((center_x - side // 2, top, center_x + side // 2, top + side))
    avatar = avatar.resize((192, 192), Image.Resampling.LANCZOS)
    avatar.save(res / "mipmap-xxxhdpi/ic_launcher.png", "PNG", optimize=True)

activity_path = root / "app/src/main/java/com/merak/app/MainActivity.kt"
src = activity_path.read_text(encoding="utf-8")

def replace_once(old, new):
    global src
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"Expected 1 Kotlin match but saw {count}: {old[:80]}")
    src = src.replace(old, new, 1)

replace_once("import kotlinx.coroutines.launch", "import kotlinx.coroutines.delay\nimport kotlinx.coroutines.launch")
replace_once("    val context = LocalContext.current\n    val store = remember { MerakStore(context) }",
             "    val context = LocalContext.current\n    var openingCover by rememberSaveable { mutableStateOf(true) }\n    LaunchedEffect(Unit) { delay(1300); openingCover = false }\n    val store = remember { MerakStore(context) }")
replace_once("    BackHandler(enabled = selectedReadingId.isNotBlank() || selectedWeb != null) { backToList() }\n    Scaffold(",
             "    BackHandler(enabled = selectedReadingId.isNotBlank() || selectedWeb != null) { backToList() }\n    if (openingCover) {\n        Box(Modifier.fillMaxSize().background(Navy), contentAlignment = Alignment.Center) {\n            Image(painterResource(R.drawable.merak_cover), contentDescription = \"MERAK açılış kapağı\",\n                contentScale = ContentScale.Fit, modifier = Modifier.fillMaxSize())\n        }\n        return\n    }\n    Scaffold(")
replace_once('    val dateText = LocalDate.now().format(DateTimeFormatter.ofPattern("d MMMM, EEEE", Locale.forLanguageTag("tr-TR")))\n    PageContent {',
             '    val dateText = LocalDate.now().format(DateTimeFormatter.ofPattern("d MMMM, EEEE", Locale.forLanguageTag("tr-TR")))\n    var coverDialogOpen by rememberSaveable { mutableStateOf(false) }\n    PageContent {')
replace_once("Box(Modifier.fillMaxWidth().height(190.dp).clip(RoundedCornerShape(20.dp))) {\n            Image(painterResource(R.drawable.merak_cover)",
             "Box(Modifier.fillMaxWidth().height(218.dp).clip(RoundedCornerShape(20.dp))\n            .clickable { coverDialogOpen = true }) {\n            Image(painterResource(R.drawable.merak_hero)")
replace_once("    }\n}\n\n@Composable\nprivate fun MoodCard(selected:",
             "    }\n    if (coverDialogOpen) {\n        androidx.compose.ui.window.Dialog(onDismissRequest = { coverDialogOpen = false }) {\n            Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp))\n                .background(Navy).padding(10.dp)) {\n                Image(painterResource(R.drawable.merak_cover), contentDescription = \"MERAK tam kapak görseli\",\n                    contentScale = ContentScale.Fit, modifier = Modifier.fillMaxWidth().aspectRatio(857f / 1536f))\n                TextButton(onClick = { coverDialogOpen = false }, modifier = Modifier.align(Alignment.End)) {\n                    Text(\"Kapat\", color = Gold, fontSize = 13.sp)\n                }\n            }\n        }\n    }\n}\n\n@Composable\nprivate fun MoodCard(selected:")
activity_path.write_text(src, encoding="utf-8")

app_build = root / "app/build.gradle.kts"
spec = app_build.read_text(encoding="utf-8")
if 'versionCode = 1' not in spec or 'versionName = "0.1.0"' not in spec:
    raise SystemExit("Unexpected version info in app/build.gradle.kts")
spec = spec.replace("versionCode = 1", "versionCode = 2").replace('versionName = "0.1.0"', 'versionName = "0.1.1"')
app_build.write_text(spec, encoding="utf-8")
print("MERAK 0.1.1 cover fix applied.")

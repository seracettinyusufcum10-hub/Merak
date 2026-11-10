from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
source_file = root / "app/src/main/java/com/merak/app/MainActivity.kt"
src = source_file.read_text(encoding="utf-8")

def replace_one(old, new):
    global src
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f"Beklenen Kotlin eşleşmesi 1, bulunan {n}: {old[:90]!r}")
    src = src.replace(old, new, 1)

replace_one(
    "    val store = remember { MerakStore(context) }\n    val pack = remember { store.content }",
    "    val store = remember { MerakStore(context) }\n    // Compose state drives this UI immediately; preferences preserve the answer for today.\n    var currentMood by remember { mutableStateOf(store.mood) }\n    val pack = remember { store.content }"
)

replace_one(
    "                            onMood = { store.mood = it; stateVersion++ }, onOpenDiscover = { tab = Tab.DISCOVER })",
    "                            selectedMood = currentMood,\n                            onMood = { choice -> currentMood = choice; store.mood = choice; stateVersion++ },\n                            onOpenDiscover = { tab = Tab.DISCOVER })"
)

replace_one(
    "    onMood: (String) -> Unit, onOpenDiscover: () -> Unit\n) {",
    "    selectedMood: String, onMood: (String) -> Unit, onOpenDiscover: () -> Unit\n) {"
)

replace_one(
    "        MoodCard(store.mood, onMood)",
    """        MoodCard(selectedMood, onMood, onExplore = {
            val preferredCategory = when (selectedMood) {
                "Zor" -> "Psikoloji"
                "İdare eder" -> "Öykü"
                "Enerjik" -> "Bilim"
                else -> "Edebiyat"
            }
            onReading(pack.readings.firstOrNull { it.category == preferredCategory }?.id ?: selection.id)
        })"""
)

replace_one(
    "            .padding(horizontal = 20.dp, vertical = 18.dp),\n        verticalArrangement = Arrangement.spacedBy(18.dp), content = content",
    "            .padding(horizontal = 18.dp, vertical = 16.dp),\n        verticalArrangement = Arrangement.spacedBy(15.dp), content = content"
)

replace_one(
    """    Column(
        modifier.fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(Panel).padding(17.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp), content = content
    )""",
    """    val shape = RoundedCornerShape(18.dp)
    Column(
        modifier.fillMaxWidth().clip(shape).background(Panel)
            .border(1.dp, Line.copy(alpha = 0.58f), shape).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(9.dp), content = content
    )"""
)

replace_one(
    "import androidx.compose.foundation.background\nimport androidx.compose.foundation.clickable",
    "import androidx.compose.foundation.background\nimport androidx.compose.foundation.border\nimport androidx.compose.foundation.clickable"
)

replace_one(
    """                Text("MERAK", color = Cream, fontFamily = FontFamily.Serif, fontSize = 28.sp, letterSpacing = 2.sp)""",
    """                Text("MERAK", color = Cream, fontFamily = FontFamily.Serif, fontSize = 27.sp, letterSpacing = 1.4.sp)
                Text("Kendine ayırdığın birkaç dakika", color = Muted, fontSize = 11.sp)"""
)

replace_one(
    """            LabelTitle("Bugün ne okuyalım?", "Ortalama birkaç dakika. İstediğin zaman bırakabilirsin.")""",
    """            LabelTitle("Günün okuması", "Birkaç dakikalık bir keşif. Acele etmene gerek yok.")"""
)

start = src.index("@Composable\nprivate fun MoodCard(")
end = src.index("@Composable\nprivate fun ReadingTile(", start)
new_card = """@Composable
private fun MoodCard(selected: String, onMood: (String) -> Unit, onExplore: () -> Unit) {
    val choices = listOf("İyi", "İdare eder", "Zor", "Enerjik")
    val advice = when (selected) {
        "İyi" -> "Güzel giden bir günü küçük bir keşifle zenginleştir. Bugün öğrendiğin tek bir fikir bile yeter."
        "İdare eder" -> "Her günü büyük bir enerjiyle geçirmek zorunda değilsin. Kısa bir öyküyle zihnini dinlendirebilirsin."
        "Zor" -> "Bugün zor geçiyorsa kendine yüklenme. Üç dakikalık sakin bir okuma bile yeterli bir adım olabilir."
        "Enerjik" -> "Bu enerjiyi merak ettiğin bir soruya yönlendir. Öğrendiğini bir cümlede anlatmayı dene."
        else -> ""
    }
    val heading = when (selected) {
        "İyi" -> "İyi hissediyorsun"
        "İdare eder" -> "Bugün biraz sakin"
        "Zor" -> "Zor bir gün olabilir"
        "Enerjik" -> "Keşfetmeye hazırsın"
        else -> ""
    }
    SurfaceCard {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween) {
            Eyebrow("KÜÇÜK BİR DURAK")
            if (selected.isNotBlank()) {
                Row(verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Icon(Icons.Default.CheckCircle, contentDescription = null,
                        tint = Green, modifier = Modifier.size(14.dp))
                    Text("Kaydedildi", color = Green, fontSize = 11.sp)
                }
            }
        }
        Text("Bugün nasılsın?", color = Cream, fontSize = 18.sp,
            fontWeight = FontWeight.SemiBold, lineHeight = 23.sp)
        Text("Nasıl hissettiğini seç. Sana uygun küçük bir adım bulalım.",
            color = Muted, fontSize = 12.sp, lineHeight = 18.sp)
        choices.chunked(2).forEach { group ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                group.forEach { mood ->
                    val active = selected == mood
                    val shape = RoundedCornerShape(12.dp)
                    Box(
                        Modifier.weight(1f).heightIn(min = 48.dp)
                            .clip(shape)
                            .background(if (active) Gold else PanelLight)
                            .border(1.dp, if (active) Gold else Line, shape)
                            .clickable { onMood(mood) }
                            .padding(horizontal = 9.dp, vertical = 13.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(mood, color = if (active) Navy else Cream, fontSize = 13.sp,
                            fontWeight = if (active) FontWeight.SemiBold else FontWeight.Medium,
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
        if (selected.isNotBlank()) {
            Column(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp))
                    .background(Navy.copy(alpha = 0.8f)).padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(heading, color = Cream, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                Text(advice, color = Muted, fontSize = 13.sp, lineHeight = 20.sp)
                OutlinedSmall("Bana uygun bir okuma aç", onExplore)
            }
        } else {
            Text("Seçimin yalnızca bu cihazda saklanır.",
                color = Muted.copy(alpha = 0.85f), fontSize = 11.sp)
        }
    }
}

"""
src = src[:start] + new_card + src[end:]
source_file.write_text(src, encoding="utf-8")

build = root / "app/build.gradle.kts"
config = build.read_text(encoding="utf-8")
if "versionCode = 2" not in config or 'versionName = "0.1.1"' not in config:
    raise RuntimeError("Unexpected version in Gradle script")
config = config.replace("versionCode = 2", "versionCode = 3").replace(
    'versionName = "0.1.1"', 'versionName = "0.1.2"')
build.write_text(config, encoding="utf-8")
print("MERAK 0.1.2: mood state, interactive recommendations and compact design applied.")

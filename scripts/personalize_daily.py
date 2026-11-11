from pathlib import Path
import sys
import json

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("source/MERAK-Android")
data_path = root / "app/src/main/java/com/merak/app/MerakData.kt"
sync_path = root / "app/src/main/java/com/merak/app/DailySync.kt"
ui_path = root / "app/src/main/java/com/merak/app/MainActivity.kt"
build_path = root / "app/build.gradle.kts"
assets_path = root / "app/src/main/assets/content.json"

def one(text, old, new, description):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{description}: expected one match, found {count}; token: {old[:90]!r}")
    return text.replace(old, new, 1)

# SharedPreferences is device-local. Nothing about the user's mood or interests
# is uploaded to a remote profile. Only public encyclopaedia searches go online.
data = data_path.read_text(encoding="utf-8")
data = one(data,
    "import kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.withContext",
    "import kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.async\nimport kotlinx.coroutines.awaitAll\nimport kotlinx.coroutines.withContext",
    "Coroutine imports")

data = one(data,
    "    // Last successful daily download remains readable without internet.",
    """    val interests: Set<String>
        get() = getSet("chosen_interests")
    var favoriteAuthors: String
        get() = prefs.getString("favorite_authors", "") ?: ""
        set(value) { prefs.edit().putString("favorite_authors", value.take(240)).remove("web_date").apply() }
    fun setInterests(values: Set<String>) {
        prefs.edit().putStringSet("chosen_interests", values.toSet()).remove("web_date").apply()
    }
    fun refreshSeed(): Int = prefs.getInt("web_refresh_seed", 0)
    fun nextRefreshSeed(): Int {
        val n = (refreshSeed() + 1) % 100000
        prefs.edit().putInt("web_refresh_seed", n).apply()
        return n
    }
    fun recentlyShownIds(): Set<String> = runCatching {
        val ids = JSONArray(prefs.getString("seen_web_ids", "[]"))
        (0 until ids.length()).map { ids.optString(it) }.toSet()
    }.getOrDefault(emptySet())

    // Last successful daily download remains readable without internet.""",
    "Persistent profile fields")

data = one(data,
    """        prefs.edit().putString("web_date", dayKey()).putString("web_stories", a.toString()).apply()""",
    """        val recent = runCatching {
            val ids = JSONArray(prefs.getString("seen_web_ids", "[]"))
            (0 until ids.length()).map { ids.optString(it) }
        }.getOrDefault(emptyList())
        val updated = (recent + stories.map { it.id }).distinct().takeLast(65)
        val json = JSONArray()
        updated.forEach { json.put(it) }
        prefs.edit().putString("web_date", dayKey())
            .putString("web_stories", a.toString())
            .putString("seen_web_ids", json.toString()).apply()""",
    "Recently shown story history")

start = data.index("    suspend fun daily(): List<WebStory> = withContext(Dispatchers.IO) {")
end = data.index("\n    suspend fun search(", start)
data = data[:start] + """    private val preferenceTopics: Map<String, List<String>> = mapOf(
        "Edebiyat" to listOf("edebiyat tarihi", "roman türü", "edebî akımlar", "dünya edebiyatı", "şiir"),
        "Öykü" to listOf("kısa öykü", "öykücülük", "hikâye anlatıcılığı", "edebiyat dergisi"),
        "Psikoloji" to listOf("bellek psikolojisi", "duygular", "algı psikolojisi", "alışkanlık", "psikoloji tarihi"),
        "Tarih" to listOf("antik uygarlıklar", "Osmanlı tarihi", "Rönesans tarihi", "arkeoloji", "dünya tarihi"),
        "Bilim" to listOf("astronomi", "biyoloji", "fizik tarihi", "nörobilim", "uzay araştırmaları"),
        "Felsefe" to listOf("Stoacılık", "etik", "varoluşçuluk", "felsefe tarihi", "mantık"),
        "Ekonomi" to listOf("iktisat tarihi", "para tarihi", "enflasyon", "ekonomik düşünce"),
        "Coğrafya" to listOf("dünya coğrafyası", "okyanuslar", "dağ oluşumu", "iklim"),
        "Sanat" to listOf("sanat tarihi", "resim sanatı", "mimarlık tarihi", "müzik tarihi"),
        "Teknoloji" to listOf("bilişim tarihi", "yapay zekâ", "internet tarihi", "robotik")
    )

    suspend fun daily(
        interests: Set<String> = emptySet(),
        favoriteAuthors: String = "",
        seenIds: Set<String> = emptySet(),
        seed: Int = 0
    ): List<WebStory> = withContext(Dispatchers.IO) {
        val day = dayNumber()
        val favorites = favoriteAuthors.split(",", ";", "\\n")
            .map { it.trim() }.filter { it.length in 3..65 }.distinct().take(6)
        val preferredTopicPool = interests.toList().sorted()
            .flatMap { preferenceTopics[it].orEmpty() }.distinct()
            .ifEmpty { topics }
        val firstAuthor = if (favorites.isNotEmpty() && Math.floorMod(day + seed, 3L) != 0L)
            favorites[Math.floorMod(day + seed.toLong(), favorites.size.toLong()).toInt()]
        else authors[Math.floorMod(day + seed.toLong(), authors.size.toLong()).toInt()]
        val otherAuthor = authors[Math.floorMod(day / 3 + seed + 17L, authors.size.toLong()).toInt()]
        val firstTopic = preferredTopicPool[
            Math.floorMod(day + seed.toLong(), preferredTopicPool.size.toLong()).toInt()]
        val secondTopic = preferredTopicPool[
            Math.floorMod(day / 2 + seed + 5L, preferredTopicPool.size.toLong()).toInt()]
        val searches = listOf(
            firstAuthor to "Yazarlar",
            firstTopic to "İlgini çekebilir",
            otherAuthor to "Edebiyat",
            secondTopic to "Bunu biliyor muydun?"
        )
        val allResults = searches.map { (query, label) ->
            async { searchBlocking(query, 4, label) }
        }.awaitAll().flatten().distinctBy { it.id }
        val unseen = allResults.filterNot { it.id in seenIds }
        (unseen + allResults).distinctBy { it.id }.take(6)
    }
""" + data[end:]
# Kotlin string split separator is a regular escaped newline char; use the char expression
data = data.replace('favoriteAuthors.split(",", ";", "\\\\n")',
                    "favoriteAuthors.split(',', ';', '\\\\n')")
data_path.write_text(data, encoding="utf-8")

sync = sync_path.read_text(encoding="utf-8")
sync = one(sync, "val items = WikiSource.daily()",
    "val items = WikiSource.daily(store.interests, store.favoriteAuthors, store.recentlyShownIds(), store.refreshSeed())",
    "Daily worker query")
sync_path.write_text(sync, encoding="utf-8")

ui = ui_path.read_text(encoding="utf-8")
ui = one(ui, 'TODAY("Günüm"), DISCOVER("Keşfet"), WORDS("Kelimeler"), YOU("Ben")',
              'TODAY("Bugün"), DISCOVER("Keşfet"), WORDS("Kelimeler"), YOU("Profil")',
              "Bottom navigation")
ui = one(ui, "val results = WikiSource.daily()",
              "val results = WikiSource.daily(store.interests, store.favoriteAuthors, store.recentlyShownIds(), if (force) store.nextRefreshSeed() else store.refreshSeed())",
              "Personalized live download")
ui = one(ui, "onOpenDiscover = { tab = Tab.DISCOVER })",
              "onOpenDiscover = { tab = Tab.DISCOVER }, onOpenProfile = { tab = Tab.YOU })",
              "Home profile route")
ui = one(ui,
    "Tab.YOU -> ProfilePage(store, onChange = { stateVersion++ })",
    "Tab.YOU -> ProfilePage(store, onChange = { stateVersion++ }, onPersonalize = { stateVersion++; refreshDaily(true) })",
    "Profile save callback")

ui = one(ui,
    "selectedMood: String, onMood: (String) -> Unit, onOpenDiscover: () -> Unit",
    "selectedMood: String, onMood: (String) -> Unit, onOpenDiscover: () -> Unit, onOpenProfile: () -> Unit",
    "Home parameters")

ui = one(ui,
    """    val todayIndex = Math.floorMod(dayNumber(), pack.readings.size.toLong()).toInt()
    val selection = pack.readings[todayIndex]""",
    """    val preferredReadings = pack.readings.filter { it.category in store.interests }
        .ifEmpty { pack.readings }
    val todayIndex = Math.floorMod(dayNumber(), preferredReadings.size.toLong()).toInt()
    val selection = preferredReadings[todayIndex]""",
    "Personalized daily reading")

ui = one(ui,
    """        MoodCard(selectedMood, onMood, onExplore = {""",
    """        if (store.interests.isEmpty()) {
            SurfaceCard {
                Eyebrow("SANA UYGUN İÇERİKLER")
                Text("Neler okumaktan hoşlanırsın?", color = Cream,
                    fontWeight = FontWeight.Medium, fontSize = 15.sp)
                Text("İlgini çeken konuları seçersen günlük okumalar ve keşifler buna göre değişir.",
                    color = Muted, fontSize = 12.sp, lineHeight = 19.sp)
                OutlinedSmall("İlgi alanlarımı seç", onOpenProfile)
            }
        }
        MoodCard(selectedMood, onMood, onExplore = {""",
    "Home onboarding")

ui = one(ui,
    'Eyebrow("İnternetten yeni keşifler")',
    'Eyebrow("Bugünün internet keşifleri")',
    "Online headline")
ui = one(ui,
    'Text("İnternet bağlantısıyla her gün farklı konular ve yazarlar geliyor.", color = Muted, fontSize = 13.sp)',
    'Text("Bağlandığında ilgi alanlarına uygun farklı konular ve yazarlar göreceksin.", color = Muted, fontSize = 13.sp)',
    "Online placeholder")

ui = one(ui,
    'LabelTitle("Dünyaya başka bir gözle bak.", "Yazarlar, fikirler, ilginç gerçekler… Tek bir isim listesine bağlı değilsin.")',
    'LabelTitle("Yeni bir şey keşfet.", "Sevdiğin konuların yanında hiç karşılaşmadığın fikirler de var.")',
    "Discover intro")

ui = one(ui,
    'Eyebrow("Her yazarı ve her konuyu ara")',
    'Eyebrow("Merak ettiğini ara")',
    "Search label")
ui = one(ui,
    'Text("İnternet sonuçları: Vikipedi. Kaynak ve lisans bilgisi içerikte görünür.", color = Muted, fontSize = 10.sp)',
    'Text("Kaynak: Türkçe Vikipedi. Daha fazlası için yazının kaynağına gidebilirsin.", color = Muted, fontSize = 10.sp)',
    "Source description")
ui = one(ui,
    'LabelTitle("Günün yeni keşifleri", "Son indirme: ',
    'LabelTitle("Her gün farklı keşifler", "Son güncelleme: ',
    "Discover daily heading")

ui = one(ui,
    'Text("Vikipedi · kaynaklı içerik", color = Gold, fontSize = 11.sp)',
    'Text("Kaynak: Vikipedi", color = Gold, fontSize = 11.sp)',
    "Source label")
ui = one(ui,
    'Eyebrow("Bir dakikalık kontrol")',
    'Eyebrow("Kısa bir soru")',
    "Quiz label")
ui = one(ui,
    'Text(if (selected == item.answer) "Doğru cevap." else "Bu kez olmadı. Birlikte öğrenelim.",',
    'Text(if (selected == item.answer) "Doğru." else "Bu kez olmadı. Açıklamaya bakalım.",',
    "Answer feedback")
ui = one(ui,
    'LabelTitle("Kelimeler", "Her gün üç kelime. Ezberlemek değil, gerçekten kullanmak önemli.")',
    'LabelTitle("Kelimeler", "Her gün üç kelime öğren, birini kendi cümlende kullan.")',
    "Words intro")
ui = one(ui,
    'Text("Bir kelimeyi bir cümlede kullanabildiğinde işaretle.", color = Muted, fontSize = 12.sp)',
    'Text("Anlamını bilmek iyi; cümle içinde kullanabilmek daha da iyi.", color = Muted, fontSize = 12.sp)',
    "Words helper")

ui = one(ui,
    """private fun ProfilePage(store: MerakStore, onChange: () -> Unit) {
    var note by rememberSaveable { mutableStateOf(store.nightNote) }""",
    """private fun ProfilePage(store: MerakStore, onChange: () -> Unit, onPersonalize: () -> Unit) {
    var note by rememberSaveable { mutableStateOf(store.nightNote) }
    var chosenTopics by remember { mutableStateOf(store.interests) }
    var authorsText by rememberSaveable { mutableStateOf(store.favoriteAuthors) }
    var preferencesSaved by remember { mutableStateOf(false) }""",
    "Profile signature and state")

ui = one(ui,
    """        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard""",
    """        SurfaceCard {
            Eyebrow("İLGİ ALANLARIN")
            Text("Neler ilgini çekiyor?", color = Cream, fontSize = 17.sp,
                fontWeight = FontWeight.SemiBold)
            Text("Birden çok konu seçebilirsin. Her gün sana uygun içerikler gösterelim.",
                color = Muted, fontSize = 12.sp, lineHeight = 19.sp)
            val options = listOf("Edebiyat", "Öykü", "Psikoloji", "Tarih", "Bilim",
                "Felsefe", "Ekonomi", "Coğrafya", "Sanat", "Teknoloji")
            options.chunked(2).forEach { pair ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    pair.forEach { topic ->
                        val active = topic in chosenTopics
                        val shape = RoundedCornerShape(12.dp)
                        Box(Modifier.weight(1f).heightIn(min = 44.dp).clip(shape)
                            .background(if (active) Gold else PanelLight)
                            .border(1.dp, if (active) Gold else Line, shape)
                            .clickable {
                                chosenTopics = if (active) chosenTopics - topic else chosenTopics + topic
                                preferencesSaved = false
                            }.padding(horizontal = 9.dp, vertical = 11.dp),
                            contentAlignment = Alignment.Center) {
                            Text(topic, color = if (active) Navy else Cream, fontSize = 12.sp,
                                fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal)
                        }
                    }
                }
            }
            Spacer(Modifier.height(3.dp))
            OutlinedTextField(value = authorsText, onValueChange = {
                authorsText = it.take(240); preferencesSaved = false
            }, modifier = Modifier.fillMaxWidth(), maxLines = 2,
                label = { Text("Merak ettiğin yazarlar (isteğe bağlı)") },
                placeholder = { Text("Örn. Kafka, Yaşar Kemal") },
                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Gold,
                    unfocusedBorderColor = Line))
            PrimaryButton("Tercihlerimi kaydet", onClick = {
                store.setInterests(chosenTopics)
                store.favoriteAuthors = authorsText
                preferencesSaved = true
                onPersonalize()
            }, modifier = Modifier.fillMaxWidth())
            if (preferencesSaved) Text("Kaydedildi. Yeni içerikler seçiliyor.",
                color = Green, fontSize = 12.sp)
            Text("Seçimlerin yalnızca telefonunda saklanır. İstediğinde değiştirebilirsin.",
                color = Muted, fontSize = 11.sp, lineHeight = 17.sp)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricCard""",
    "Preference selector widget")

ui_path.write_text(ui, encoding="utf-8")

# Wording audit for a few awkward vocabulary examples. Avoid adding new claims.
asset = json.loads(assets_path.read_text(encoding="utf-8"))
changes = {
    "Muhakeme": ("Önce olasılıkları değerlendirdi, sonra karar verdi.", "Akıl yürütme."),
    "Sürtünme": ("İşe başlamadan önceki uzun hazırlık süreci onu yavaşlattı.", "Bu kullanımda: ilerlemeyi zorlaştıran engel."),
    "Projeksiyon": ("Farklı harita projeksiyonları şekilleri ve alanları değiştirebilir.", "Harita çiziminde: yansıtma yöntemi."),
    "İmparatorluk": ("İmparatorluk, çok farklı toplulukları bir arada yönetiyordu.", "Geniş topraklara yayılan devlet."),
    "Birikim": ("Her gün okuduğu kısa yazılar zamanla bilgi birikimini artırdı.", "Zaman içinde toplanan değer."),
    "Yayılım": ("Yeni fikrin yayılımı internet sayesinde hızlandı.", "Yayılma.")
}
for word in asset.get("words", []):
    if word.get("word") in changes:
        word["example"], word["alternative"] = changes[word["word"]]
assets_path.write_text(json.dumps(asset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build = build_path.read_text(encoding="utf-8")
build = one(build, "versionCode = 3", "versionCode = 4", "Version code")
build = one(build, 'versionName = "0.1.2"', 'versionName = "0.1.3"', "Version name")
build_path.write_text(build, encoding="utf-8")

print("MERAK 0.1.3: interests, authors, rotating daily articles and Turkish wording applied.")

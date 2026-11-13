package com.merak.app

import android.content.Context
import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.time.LocalDate

/**
 * Offline, user-controlled JSON backup. A backup is readable text, not encrypted.
 * Restore merges progress and never replaces existing notes silently.
 */
object MerakBackup {
    private const val PREFS = "merak_local_v1"
    private const val FORMAT = "MERAK_BACKUP"
    private const val MAX_BYTES = 2 * 1024 * 1024
    private const val MAX_KEYS = 2000
    private val setKeys = setOf("read_ids", "saved_ids", "known_words",
        "completed_days", "chosen_interests")

    private fun validDate(date: String): Boolean =
        date.matches(Regex("\\d{4}-\\d{2}-\\d{2}")) &&
            runCatching { LocalDate.parse(date) }.isSuccess

    private fun validKey(key: String, value: Any): Boolean = when {
        key in setKeys -> value is Set<*> && value.size <= 3000 &&
            value.all { it is String && it.length in 1..100 }
        key == "favorite_authors" -> value is String && value.length <= 240
        key.startsWith("mood_") && validDate(key.removePrefix("mood_")) ->
            value is String && value.length <= 60
        key.startsWith("note_") && validDate(key.removePrefix("note_")) ->
            value is String && value.length <= 10000
        key.startsWith("bedtime_") && validDate(key.removePrefix("bedtime_")) ->
            value is Boolean
        else -> false
    }

    private fun source(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun exportText(context: Context): String {
        val entries = JSONObject()
        for ((key, value) in source(context).all.toSortedMap()) {
            if (value == null || !validKey(key, value)) continue
            when (value) {
                is Set<*> -> entries.put(key, JSONArray(value.filterIsInstance<String>().sorted()))
                else -> entries.put(key, value)
            }
        }
        val result = JSONObject()
            .put("format", FORMAT)
            .put("version", 1)
            .put("entries", entries)
            .toString(2)
        require(result.toByteArray(Charsets.UTF_8).size <= MAX_BYTES) {
            "Yedek dosyası izin verilen boyutu aşıyor."
        }
        return result
    }

    fun write(context: Context, uri: Uri) {
        val text = exportText(context)
        context.contentResolver.openOutputStream(uri, "wt")?.use { stream ->
            stream.write(text.toByteArray(Charsets.UTF_8))
            stream.flush()
        } ?: error("Dosya yazmak için açılamadı.")
    }

    fun read(context: Context, uri: Uri): String {
        val stream = context.contentResolver.openInputStream(uri)
            ?: error("Dosya açılamadı.")
        val output = ByteArrayOutputStream()
        stream.use { input ->
            val buffer = ByteArray(8192)
            while (true) {
                val n = input.read(buffer)
                if (n < 0) break
                if (output.size() + n > MAX_BYTES) error("Yedek dosyası çok büyük.")
                output.write(buffer, 0, n)
            }
        }
        val text = output.toString("UTF-8")
        parse(text)
        return text
    }

    private fun parse(text: String): Map<String, Any> {
        require(text.toByteArray(Charsets.UTF_8).size <= MAX_BYTES) {
            "Yedek dosyası çok büyük."
        }
        val root = JSONObject(text)
        require(root.optString("format") == FORMAT && root.optInt("version") == 1) {
            "Bu dosya MERAK yedeği değil veya desteklenmeyen sürümde."
        }
        val entries = root.getJSONObject("entries")
        require(entries.length() <= MAX_KEYS) { "Yedek çok fazla kayıt içeriyor." }
        val valid = LinkedHashMap<String, Any>()
        val iterator = entries.keys()
        while (iterator.hasNext()) {
            val key = iterator.next()
            val raw = entries.get(key)
            val value: Any = if (key in setKeys && raw is JSONArray) {
                require(raw.length() <= 3000) { "Yedekte çok fazla kayıt var." }
                (0 until raw.length()).map { raw.getString(it) }.toSet()
            } else raw
            require(validKey(key, value)) { "Geçersiz veya desteklenmeyen yedek alanı." }
            valid[key] = value
        }
        return valid
    }

    fun inspect(text: String): String {
        val items = parse(text)
        val notes = items.keys.count { it.startsWith("note_") }
        val interests = (items["chosen_interests"] as? Set<*>)?.size ?: 0
        return "\${items.size} kayıt, \$notes not, \$interests ilgi alanı."
    }

    /**
     * Merge rather than replace. Keeps the current device's nonempty notes,
     * favorite authors, and existing choices. Unions read/word progress.
     */
    fun restore(context: Context, text: String): Int {
        val incoming = parse(text)
        val prefs = source(context)
        val editor = prefs.edit()
        var changes = 0
        for ((key, value) in incoming) {
            when (value) {
                is Set<*> -> {
                    val old = prefs.getStringSet(key, emptySet()).orEmpty()
                    val merged = old + value.filterIsInstance<String>()
                    if (merged != old) {
                        editor.putStringSet(key, merged.toSet())
                        changes++
                    }
                }
                is String -> {
                    if (prefs.getString(key, "").isNullOrBlank() && value.isNotBlank()) {
                        editor.putString(key, value)
                        changes++
                    }
                }
                is Boolean -> {
                    if (value && !prefs.getBoolean(key, false)) {
                        editor.putBoolean(key, true)
                        changes++
                    }
                }
            }
        }
        if (!editor.commit()) error("Yedek geri yüklenemedi.")
        return changes
    }
}

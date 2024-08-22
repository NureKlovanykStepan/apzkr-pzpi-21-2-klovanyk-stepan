package com.example.feelthebook.utils.auth

import com.franmontiel.persistentcookiejar.PersistentCookieJar
import com.franmontiel.persistentcookiejar.cache.CookieCache
import com.franmontiel.persistentcookiejar.persistence.CookiePersistor
import okhttp3.Cookie
import okhttp3.HttpUrl

class ModifiedPersistentCookieJar(
    private val cache: CookieCache,
    private val persistor: CookiePersistor,
) : PersistentCookieJar(
    cache, persistor
) {
    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        cache.addAll(cookies)
        persistor.saveAll(cookies)
    }
}
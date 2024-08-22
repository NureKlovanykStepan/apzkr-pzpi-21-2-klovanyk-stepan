package com.example.feelthebook.utils.auth

import android.util.Base64

class BasicAuthCredentialsEncoder {
    fun encode(username: String, password: String): String {
        val credentials = "$username:$password"
        val encodedCredentials = Base64.encodeToString(
            credentials.toByteArray(), Base64.NO_WRAP
        )

        return "Basic $encodedCredentials"
    }
}
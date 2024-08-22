package com.example.feelthebook.utils.retrofit

import retrofit2.Response

fun <T> Response<T>.toFailedCodeAndResponse(): Pair<Int, String>? =
    if (isSuccessful) null else (code() to (errorBody()?.let { errorBody ->
        errorBody
            .string()
            .apply { errorBody.close() }
    } ?: "Unknown error"))

fun <T> Response<T>.toSuccessCodeAndResponse(): Pair<Int, T>? =
    if (isSuccessful) (code() to body()!!) else null
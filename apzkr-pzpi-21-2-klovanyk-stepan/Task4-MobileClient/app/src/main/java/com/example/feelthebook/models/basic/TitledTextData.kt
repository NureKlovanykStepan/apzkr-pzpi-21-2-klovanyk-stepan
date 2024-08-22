package com.example.feelthebook.models.basic

data class TitledTextData(
    val title: String,
    val message: String,
) {
    companion object {
        fun fromPair(pair: Pair<String, String>) = TitledTextData(
            pair.first, pair.second
        )
    }
}
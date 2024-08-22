package com.example.feelthebook.models.basic

import com.example.feelthebook.LiteratureFetchingMode

data class LiteraturesFilteringSortingData(
    val page: Int,
    val mode: LiteratureFetchingMode,
    val genres: List<String>,
    val authors: List<Int>,
    val type: String?,
    val maxOnPage: Int,
    val query: String? = null,
) {
    data class RequestData(
        val offset: Int,
        val maxCount: Int,
        val filter: List<String>,
        val joins: List<String>,
        val multiGenres: List<String>,
    )

    fun toRequestData() = RequestData(
        offset = (page - 1) * maxOnPage,
        maxCount = maxOnPage,
        filter = getFilterData(),
        joins = getJoinsData(),
        multiGenres = getMultiGenre(),
    )

    private fun getJoinsData() = listOfNotNull(
        *genres.firstOrNull()
            ?.let {
                arrayOf(
                    "literature_genre",
                    "genre"
                )
            } ?: emptyArray<String>(),
        *authors.firstOrNull()
            ?.let {
                arrayOf(
                    "literature_author",
                    "author"
                )
            } ?: emptyArray<String>(),
    )

    private fun getFilterData() = listOfNotNull(
        *authors.map { "author.id=${it}" }
            .toTypedArray(),
        type?.let { "type_name=${it}" },
        query.takeIf { !it.isNullOrBlank() }
            ?.let { "name~${it}" }
    )

    private fun getMultiGenre() = genres
}
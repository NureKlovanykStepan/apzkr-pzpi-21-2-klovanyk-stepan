package com.example.feelthebook.models.basic.singleton

import com.example.feelthebook.models.basic.ThumbnailData

object ThumbnailsCache {
    private var _size = 150
    private var _storage: Map<Int, ThumbnailData> = emptyMap()
    val storage get() = _storage
    fun getSize() = _size
    suspend fun setSize(size: Int) {
        _size = size
        _storage
            .filterWithImageDataOnly()
            .takeLastWithinRange()
            .store()
    }

    fun storeThumbnailsData(thumbnails: Map<Int, ThumbnailData>) =
        _storage
            .plus(thumbnails)
            .filterWithImageDataOnly()
            .takeLastWithinRange()
            .store()

    private fun Map<Int, ThumbnailData>.filterWithImageDataOnly() =
        filter { it.value.image != null }

    private fun Map<Int, ThumbnailData>.takeLastWithinRange() =
        toList()
            .takeLast(_size)
            .toMap()

    private fun Map<Int, ThumbnailData>.store() {
        _storage = this
    }

}
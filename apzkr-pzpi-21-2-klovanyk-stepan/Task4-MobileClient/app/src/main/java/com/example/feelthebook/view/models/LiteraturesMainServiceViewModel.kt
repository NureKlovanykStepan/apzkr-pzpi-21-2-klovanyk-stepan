package com.example.feelthebook.view.models

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.feelthebook.LiteratureFetchingMode
import com.example.feelthebook.models.basic.ThumbnailData
import com.example.feelthebook.models.basic.LiteraturesFilteringSortingData
import com.example.feelthebook.models.basic.singleton.ThumbnailsCache
import com.example.feelthebook.models.retrofit.moshi.Literature
import com.example.feelthebook.models.retrofit.services.APILiteraturesPreviewService
import com.example.feelthebook.utils.emitErrorFromResponseFailure
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import retrofit2.Response
import javax.inject.Inject

@HiltViewModel
class LiteraturesMainServiceViewModel @Inject constructor(
    private val apiLiteraturesPreviewService: APILiteraturesPreviewService,
    private val thumbnailsCache: ThumbnailsCache,
) : ViewModel() {
    private var pageLiteratures: MutableStateFlow<List<Literature>> =
        MutableStateFlow(emptyList())
    private var pageThumbnails: MutableStateFlow<Map<Int, ThumbnailData>> =
        MutableStateFlow(emptyMap())

    val literaturesRenderData: StateFlow<Map<Literature, ThumbnailData>> =
        combine(
            pageLiteratures,
            pageThumbnails
        ) { literatures, thumbnails ->
            literatures.associateWith {
                (thumbnails[it.id] ?: ThumbnailData(
                    null,
                    "Not loaded yet"
                ))
            }
        }.stateIn(
            viewModelScope,
            SharingStarted.Eagerly,
            emptyMap()
        )
    val maxOnPage = 24
    private var _sortingAndFilteringData: MutableStateFlow<LiteraturesFilteringSortingData> =
        MutableStateFlow(
            LiteraturesFilteringSortingData(
                page = 1,
                mode = LiteratureFetchingMode.All,
                genres = emptyList(),
                authors = emptyList(),
                type = null,
                maxOnPage = maxOnPage
            )
        )
    val sortingAndFilteringData = _sortingAndFilteringData.asStateFlow()

    fun updateSortingAndFiltering(
        body: LiteraturesFilteringSortingData.() -> LiteraturesFilteringSortingData,
    ) = viewModelScope.launch(Dispatchers.IO) {
        _sortingAndFilteringData.emit(_sortingAndFilteringData.value.body())
    }

    fun loadLiteratures() = viewModelScope.launch(Dispatchers.IO) {
        _sortingAndFilteringData.first()
            .run {
                when (mode) {
                    LiteratureFetchingMode.All -> fetchAll()
                    LiteratureFetchingMode.Available -> fetchAvailable()
                }.run {
                    when (isSuccessful) {
                        true -> performRenderDataUpdate()
                        false -> emitErrorFromResponseFailure("Failed to load literatures")
                    }
                }
            }
    }

    private suspend fun Response<List<Literature>>.performRenderDataUpdate() {
        pageThumbnails.value.cache()
        this.useToReloadPageData()
    }

    private fun Map<Int, ThumbnailData>.cache() =
        ThumbnailsCache.storeThumbnailsData(this)

    private suspend fun Response<List<Literature>>.useToReloadPageData() {
        body()!!.run {
            takeAsPreviewLiteratures()
            takeForPreviewThumbnailsLoading()
        }

    }

    private suspend fun List<Literature>.takeAsPreviewLiteratures() =
        pageLiteratures.emit(this)

    private suspend fun List<Literature>.takeForPreviewThumbnailsLoading() =
        pageThumbnails.emit(loadThumbnailsFromLiteratures(this))

    private fun loadThumbnailsFromLiteratures(newLiterature: List<Literature>) =
        newLiterature
            .associate {
                it.id to (ThumbnailsCache.storage[it.id]
                    ?: ThumbnailState.Unloaded.toThumbnailData())
            }


    private suspend fun LiteraturesFilteringSortingData.fetchAll() =
        fetchLiteraturesData(
            toRequestData(),
            apiLiteraturesPreviewService::getAllLiteratures
        )

    private suspend fun LiteraturesFilteringSortingData.fetchAvailable() =
        fetchLiteraturesData(
            toRequestData(),
            apiLiteraturesPreviewService::getAvailableLiteratures
        )

    private suspend fun fetchLiteraturesData(
        requestData: LiteraturesFilteringSortingData.RequestData,
        fetcher: suspend (
            join: List<String>,
            filter: List<String>,
            maxCount: Int,
            offset: Int,
            havingGenre: List<String>,
        ) -> Response<List<Literature>>,
    ) = with(requestData) {
        fetcher(
            joins,
            filter,
            maxOnPage,
            offset,
            multiGenres
        )
    }

    val previewWidth = 300

    suspend fun getPreviewThumbnail(literatureId: Int) =
        apiLiteraturesPreviewService.getThumbnail(
            literatureId,
            previewWidth
        )

    private enum class ThumbnailState {
        Unloaded,
        Loading,
        SuccessfullyLoaded;

        override fun toString(): String = when (this) {
            Unloaded -> "Hasn't been loaded yet"
            Loading -> "Loading..."
            SuccessfullyLoaded -> "Loaded successfully"
        }

        fun toThumbnailData(bitmapResult: Bitmap? = null) = ThumbnailData(
            bitmapResult,
            toString()
        )
    }


    fun loadThumbnails(literatureIds: List<Int>) {
        viewModelScope.launch(Dispatchers.IO) {
            val thumbnailsDataChannel = Channel<Pair<Int, ThumbnailData>>()
            val requestFutures = literatureIds
                .filter { pageThumbnails.value[it]?.image == null }
                .map { id ->
                    async {
                        thumbnailsDataChannel.send(id to ThumbnailState.Loading.toThumbnailData())
                        with(getPreviewThumbnail(id)) {
                            (body()?.use { BitmapFactory.decodeStream(it.byteStream()) }
                                ?.let { id to ThumbnailState.SuccessfullyLoaded.toThumbnailData(it) }
                                ?: errorBody()!!.run {
                                    when {
                                        string().contains("RESOURCE_NOT_FOUND")
                                        -> "Resource not found"

                                        else -> string()
                                    }.let { s -> id to ThumbnailData(null, s) }
                                }).run { thumbnailsDataChannel.send(this) }
                        }
                    }
                }
            launch {
                for ((id, thumbnailData) in thumbnailsDataChannel) {
                    pageThumbnails.emit(
                        pageThumbnails.value + (id to thumbnailData)
                    )
                }
            }
            awaitAll(*requestFutures.toTypedArray()).run { thumbnailsDataChannel.close() }
        }
    }
}
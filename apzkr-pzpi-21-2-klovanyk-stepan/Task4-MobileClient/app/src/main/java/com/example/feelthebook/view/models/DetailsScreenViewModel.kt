package com.example.feelthebook.view.models

import android.graphics.BitmapFactory
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.feelthebook.models.basic.ThumbnailData
import com.example.feelthebook.models.basic.TitledTextData
import com.example.feelthebook.models.basic.singleton.ErrorDataFlowStorage
import com.example.feelthebook.models.retrofit.moshi.Literature
import com.example.feelthebook.models.retrofit.services.APILiteraturesPreviewService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DetailsScreenViewModel @Inject constructor(
    private val apiLiteraturesPreviewService: APILiteraturesPreviewService,
) : ViewModel() {
    private var _detailsLiterature: MutableStateFlow<Pair<Literature, ThumbnailData>?> =
        MutableStateFlow(null)
    val detailsLiterature = _detailsLiterature.asStateFlow()

    fun setDetails(details: Pair<Literature, ThumbnailData>) = viewModelScope.launch {
        _detailsLiterature.emit(details)
        loadHighResThumbnail(details.first.id)
    }

    fun loadHighResThumbnail(literatureId: Int) = viewModelScope.launch {
        with(apiLiteraturesPreviewService.getThumbnail(literatureId, 4000)) {
            body()
                ?.use { BitmapFactory.decodeStream(it.byteStream()) }
                ?.let {
                    _detailsLiterature.first { it?.first != null }!!
                        .let { (l, td) ->
                            l to td.copy(image = it)
                        }
                }
                .also { _detailsLiterature.emit(it) }
                ?: errorBody()!!.run {
                    ErrorDataFlowStorage.emitError(
                        TitledTextData(
                            "Unable to load thumbnail in high resolution",
                            string()
                        )
                    )
                }
        }
    }
}
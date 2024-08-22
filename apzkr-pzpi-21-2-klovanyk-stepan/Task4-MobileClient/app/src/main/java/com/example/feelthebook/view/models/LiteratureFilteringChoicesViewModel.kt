package com.example.feelthebook.view.models

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.feelthebook.models.retrofit.moshi.Author
import com.example.feelthebook.models.retrofit.moshi.Genre
import com.example.feelthebook.models.retrofit.moshi.LiteratureType
import com.example.feelthebook.models.retrofit.services.APIConstantsService
import com.example.feelthebook.utils.emitErrorFromResponseFailure
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.Response
import javax.inject.Inject

@HiltViewModel
class LiteratureFilteringChoicesViewModel @Inject constructor(
    private val apiConstantsService: APIConstantsService,
) : ViewModel() {
    private var _genres: MutableStateFlow<Map<Genre, Boolean>> =
        MutableStateFlow(emptyMap())
    private var _authors: MutableStateFlow<Map<Author, Boolean>> =
        MutableStateFlow(emptyMap())
    private var _literatureTypes: MutableStateFlow<Map<LiteratureType, Boolean>> =
        MutableStateFlow(emptyMap())

    val genres = _genres.asStateFlow()
    val authors = _authors.asStateFlow()
    val literatureTypes = _literatureTypes.asStateFlow()

    init {
        reloadFilters()
    }

    fun reloadFilters() = viewModelScope.launch {
        _genres.emit(
            apiConstantsService
                .getAvailableGenres()
                .bodyOrEmitError("Genres load failed")
                ?.associate { it to false } ?: mapOf()
        )
        _authors.emit(apiConstantsService
            .getAvailableAuthors()
            .bodyOrEmitError("Authors load failed")
            ?.associate { it to false } ?: mapOf()
        )
        _literatureTypes.emit(apiConstantsService
            .getAvailableLiteratureTypes()
            .bodyOrEmitError("Literature types load failed")
            ?.associate { it to false } ?: mapOf()
        )
    }

    fun updateGenre(genre: Genre, isSelected: Boolean) = viewModelScope.launch {
        _genres.emit(_genres.value.plus(genre to isSelected))
    }

    fun updateAuthor(author: Author, isSelected: Boolean) {
        _authors.value = _authors.value.plus(author to isSelected)
    }

    fun updateLiteratureType(literatureType: LiteratureType, isSelected: Boolean) {
        _literatureTypes.value = _literatureTypes.value.plus(literatureType to isSelected)
    }

    private suspend fun <T> Response<T>.bodyOrEmitError(title: String) =
        takeIf { isSuccessful }?.body() ?: emitErrorFromResponseFailure(title).let { null }

}
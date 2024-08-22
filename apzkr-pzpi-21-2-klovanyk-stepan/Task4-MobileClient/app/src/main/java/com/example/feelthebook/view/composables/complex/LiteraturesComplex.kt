package com.example.feelthebook.view.composables.complex

import androidx.compose.animation.AnimatedContentScope
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.SearchBar
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavBackStackEntry
import androidx.navigation.NavHostController
import com.example.feelthebook.LiteratureFetchingMode
import com.example.feelthebook.view.composables.elements.literature.Literatures
import com.example.feelthebook.models.basic.enums.PageAction
import com.example.feelthebook.view.composables.elements.PageControls
import com.example.feelthebook.models.navigation.NavDestinations
import com.example.feelthebook.models.retrofit.moshi.Literature
import com.example.feelthebook.view.composables.elements.ItemsSelectableRow
import com.example.feelthebook.view.models.DetailsScreenViewModel
import com.example.feelthebook.view.models.LiteratureFilteringChoicesViewModel
import com.example.feelthebook.view.models.LiteraturesMainServiceViewModel
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.first

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnimatedContentScope.LiteraturesComplex(
    navBackStackEntry: NavBackStackEntry,
    navController: NavHostController,
    fetchingMode: LiteratureFetchingMode,
    onReadClick: ((Literature) -> Unit)?,
) {
    val parentEntry = remember(navBackStackEntry) {
        navController.getBackStackEntry(NavDestinations.Literatures)
    }

    val detailsScreenViewModel: DetailsScreenViewModel = hiltViewModel(parentEntry)
    val literaturesMainServiceViewModel: LiteraturesMainServiceViewModel =
        hiltViewModel(parentEntry)
    val constantsViewModel: LiteratureFilteringChoicesViewModel = hiltViewModel(parentEntry)

    val literaturesData by literaturesMainServiceViewModel.literaturesRenderData.collectAsState()
    val sortingAndFilteringData by literaturesMainServiceViewModel.sortingAndFilteringData.collectAsState()

    LaunchedEffect(true) {
        literaturesMainServiceViewModel.updateSortingAndFiltering {
            copy(mode = fetchingMode)
        }
        literaturesMainServiceViewModel.loadLiteratures()
    }

    fun onPageChange(pageAction: PageAction) {
        literaturesMainServiceViewModel.updateSortingAndFiltering {
            when (pageAction) {
                PageAction.PREV -> copy(page = page - 1)
                PageAction.NEXT -> copy(page = page + 1)
            }
        }
    }

    LaunchedEffect(sortingAndFilteringData) {
        snapshotFlow { sortingAndFilteringData }
            .distinctUntilChanged { old, new ->
                old.page == new.page
            }
            .debounce(250)
            .first()
            .let { literaturesMainServiceViewModel.loadLiteratures() }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        var searchBarQuery by remember { mutableStateOf("") }
        val focusManager = LocalFocusManager.current
        var advancedSearchVisibilityState by remember { mutableStateOf(false) }
        val animatedAppearance by animateFloatAsState(
            if (advancedSearchVisibilityState) 0f else 1f,
            label = "rotation"
        )

        val genres by constantsViewModel.genres.collectAsState()
        val authors by constantsViewModel.authors.collectAsState()
        val literatureTypes by constantsViewModel.literatureTypes.collectAsState()

        fun onSearchClicked(queryFromDirectClick: String? = null) {
            focusManager.clearFocus()
            advancedSearchVisibilityState = false
            literaturesMainServiceViewModel.updateSortingAndFiltering {
                copy(
                    query = (queryFromDirectClick ?: searchBarQuery).takeIf { it.isNotBlank() },
                    genres = genres.filterValues { it }
                        .map { it.key.name },
                    authors = authors.filterValues { it }
                        .map { it.key.id },
                    type = literatureTypes.filterValues { it }
                        .map { it.key.name }
                        .firstOrNull(),
                )
            }
            literaturesMainServiceViewModel.loadLiteratures()
        }
        SearchBar(
            windowInsets = WindowInsets(0.dp),
            query = searchBarQuery,
            onQueryChange = { searchBarQuery = it },
            onSearch = ::onSearchClicked,
            active = false,
            onActiveChange = { },
            placeholder = { Text("Search for literature") },
            leadingIcon = {
                IconButton(onClick = ::onSearchClicked) {
                    Icon(
                        Icons.Filled.Search,
                        contentDescription = "Search"
                    )
                }
            },
            trailingIcon = {
                IconButton(onClick = {
                    advancedSearchVisibilityState = !advancedSearchVisibilityState
                    if (genres.isEmpty()) constantsViewModel.reloadFilters()
                }) {
                    Icon(
                        Icons.Filled.ArrowDropDown,
                        contentDescription = "Sort&Filter",
                        Modifier.rotate(animatedAppearance * 180)
                    )
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {}
        AnimatedVisibility(
            visible = advancedSearchVisibilityState,
            Modifier.wrapContentSize()
        ) {
            Column {
                Column {
                    Text("Select genres")
                    ItemsSelectableRow(
                        isMulti = true,
                        itemsAndStates = genres.toList()
                            .toTypedArray()
                            .sortedBy { it.first.name }
                            .toMap(),
                        itemTextProvider = { it.name },
                        onItemClicked = { genre, isSelected ->
                            constantsViewModel.updateGenre(
                                genre,
                                !isSelected
                            )
                        }
                    )
                }
                Column {
                    Text("Select author")
                    ItemsSelectableRow(
                        isMulti = false,
                        itemsAndStates = authors
                            .toList()
                            .toTypedArray()
                            .sortedBy { it.first.pseudonym }
                            .toMap(),
                        itemTextProvider = {
                            it.pseudonym + (
                                    listOf(
                                        it.name,
                                        it.surname
                                    ).map { it.takeUnless { it.isNullOrBlank() } }
                                        .mapNotNull { it }
                                        .joinToString(" ")
                                        .takeIf { it.isNotBlank() }
                                        ?.let { " ($it)" } ?: ""
                                    )
                        },
                        onItemClicked = { author, isSelected ->
                            constantsViewModel.updateAuthor(
                                author,
                                !isSelected
                            )
                        }
                    )
                }
                Column {
                    Text("Select type")
                    ItemsSelectableRow(
                        isMulti = false,
                        itemsAndStates = literatureTypes
                            .toList()
                            .toTypedArray()
                            .sortedBy { it.first.name }
                            .toMap(),
                        itemTextProvider = { it.name },
                        onItemClicked = { type, isSelected ->
                            constantsViewModel.updateLiteratureType(
                                type,
                                !isSelected
                            )
                        }

                    )

                }
            }
        }
        Box(Modifier.weight(1f)) {
            Literatures(
                literaturesData,
                { literaturesMainServiceViewModel.loadThumbnails(it) },
                { literature, thumbnailData ->
                    detailsScreenViewModel.setDetails(literature to thumbnailData)
                    navController.navigate(NavDestinations.Literatures.Details)
                },
                onReadClick
            )
        }
        PageControls(
            pageNumber = sortingAndFilteringData.page,
            onPageChanged = ::onPageChange,
            isPrevAvailable = { sortingAndFilteringData.page > 1 },
            isNextAvailable = { literaturesData.size == literaturesMainServiceViewModel.maxOnPage }
        )
    }

}
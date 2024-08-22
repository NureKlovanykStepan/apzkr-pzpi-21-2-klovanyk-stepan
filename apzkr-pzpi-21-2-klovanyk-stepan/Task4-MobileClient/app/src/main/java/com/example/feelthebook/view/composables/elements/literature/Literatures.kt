package com.example.feelthebook.view.composables.elements.literature

import android.util.Log
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.lazy.staggeredgrid.LazyVerticalStaggeredGrid
import androidx.compose.foundation.lazy.staggeredgrid.StaggeredGridCells
import androidx.compose.foundation.lazy.staggeredgrid.items
import androidx.compose.foundation.lazy.staggeredgrid.rememberLazyStaggeredGridState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.feelthebook.models.basic.ThumbnailData
import com.example.feelthebook.models.retrofit.moshi.Literature
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged

@Composable
fun Literatures(
    literaturesData: Map<Literature, ThumbnailData>,
    onVisibleLiteraturesChange: (List<Int>) -> Unit,
    onDetailsClick: (Literature, ThumbnailData) -> Unit,
    onReadClick: ((Literature) -> Unit)?,
) {
    Box {
        Column {
            val state = rememberLazyStaggeredGridState()
            LaunchedEffect(state) {
                snapshotFlow {
                    state.layoutInfo.visibleItemsInfo
                }.debounce(1500)
                    .distinctUntilChanged { old, new ->
                        val old_compare = old.map { it.key as Int }
                            .sorted()
                        val new_compare = new.map { it.key as Int }
                            .sorted()
                        Log.d(
                            "literatures",
                            "$old_compare $new_compare ${old_compare == new_compare}"
                        )
                        old_compare == new_compare
                    }
                    .collect {
                        onVisibleLiteraturesChange(it.map { it.key as Int })
                    }
            }


            LazyVerticalStaggeredGrid(
                columns = StaggeredGridCells.Fixed(2),
                state = state,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalItemSpacing = 8.dp
            ) {
                items(literaturesData.toList(),
                    key = { it.first.id }) {
                    LiteratureItem(
                        it.first,
                        it.second,
                        onDetailsClick,
                        onReadClick
                    )
                }
            }
        }
    }
}
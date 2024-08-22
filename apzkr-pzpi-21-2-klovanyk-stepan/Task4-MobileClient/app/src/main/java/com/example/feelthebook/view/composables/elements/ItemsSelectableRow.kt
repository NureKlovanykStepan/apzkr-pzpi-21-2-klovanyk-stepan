package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun <T> ItemsSelectableRow(
    isMulti: Boolean,
    itemsAndStates: Map<T, Boolean>,
    itemTextProvider: (T) -> String,
    onItemClicked: (item: T, currentState: Boolean) -> Unit,
) {
    val othersDisabled = remember(itemsAndStates) {
        if (isMulti) false
        else itemsAndStates.values.any { it }
    }
    LazyRow(
        Modifier,
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        items(itemsAndStates.toList()) { (item, isSelected) ->
            ElevatedCard(
                onClick = {
                    onItemClicked(
                        item,
                        isSelected
                    )
                },
                colors = CardDefaults.elevatedCardColors()
                    .let {
                        if (isSelected) it.copy(
                            containerColor = MaterialTheme.colorScheme.primary,
                            contentColor = MaterialTheme.colorScheme.onPrimary
                        ) else it
                    },
                enabled = !othersDisabled || isSelected
            ) {
                Text(
                    itemTextProvider(item),
                    Modifier.padding(4.dp)
                )
            }
        }
    }
}
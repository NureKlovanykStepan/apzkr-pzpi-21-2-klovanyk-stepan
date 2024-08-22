package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalMinimumInteractiveComponentEnforcement
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.feelthebook.models.basic.enums.PageAction

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PageControls(
    pageNumber: Int,
    onPageChanged: (PageAction) -> Unit,
    isPrevAvailable: () -> Boolean,
    isNextAvailable: () -> Boolean,
    modifier: Modifier = Modifier,
) {
    CompositionLocalProvider(
        LocalMinimumInteractiveComponentEnforcement provides false
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .then(modifier),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = { onPageChanged(PageAction.PREV) },
                enabled = isPrevAvailable()
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowBack,
                    null,
                )
            }
            Text("Page #${pageNumber}")
            IconButton(
                onClick = { onPageChanged(PageAction.NEXT) },
                enabled = isNextAvailable()
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.ArrowForward,
                    null,
                )
            }
        }
    }
}
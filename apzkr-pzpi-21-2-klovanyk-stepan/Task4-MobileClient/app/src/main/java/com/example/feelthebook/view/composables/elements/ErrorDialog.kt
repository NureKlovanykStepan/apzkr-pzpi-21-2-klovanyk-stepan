package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Composable
fun ErrorDialog(
    titleText: String,
    message: String,
    onDismissRequest: () -> Unit,
) {
    return AlertDialog(onDismissRequest = onDismissRequest, confirmButton = {
        Button(onClick = onDismissRequest) {
            Text(text = "OK")
        }
    }, title = { Text(text = titleText) }, icon = {
        Icon(
            Icons.Default.Warning, contentDescription = "Error"
        )
    },

        text = {
            val currentConfig = LocalConfiguration.current
            Text(
                text = message, Modifier
                    .height(currentConfig.screenHeightDp.dp / 4)
                    .verticalScroll(rememberScrollState())
            )
        })
}

@Composable
@Preview
fun ErrorDialogPreview() {
    ErrorDialog(titleText = "Test error", message = "Test", onDismissRequest = {})
}
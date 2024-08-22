package com.example.feelthebook.view.composables.elements

import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.input.TextFieldState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp

@Composable
@OptIn(
    ExperimentalMaterial3Api::class
)
fun PrettyBasicTextField(
    textFieldState: TextFieldState,
    modifier: Modifier = Modifier,
    interactionSource: MutableInteractionSource,
    label: @Composable (() -> Unit),
) {
    return BasicTextField(modifier = Modifier
        .padding(
            0.dp, 6.dp, 0.dp, 0.dp
        )
        .then(modifier),
        textStyle = LocalTextStyle.current.copy(color=MaterialTheme.colorScheme.onSurface),
        interactionSource = interactionSource,
        state = textFieldState,
        decorator = { innerTextField ->
            OutlinedTextFieldDefaults.DecorationBox(
                value = textFieldState.text.toString(),
                innerTextField = innerTextField,
                enabled = true,
                singleLine = true,
                label = { label() },
                visualTransformation = VisualTransformation.None,
                interactionSource = interactionSource,
                container = {
                    OutlinedTextFieldDefaults.ContainerBox(
                        enabled = true, isError = false, interactionSource = interactionSource,
                        colors = OutlinedTextFieldDefaults.colors(),
                        shape = MaterialTheme.shapes.small
                    )
                },
            )

        })
}
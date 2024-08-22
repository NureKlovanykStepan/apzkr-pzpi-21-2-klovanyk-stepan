package com.example.feelthebook.view.composables.elements.literature

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import com.example.feelthebook.models.basic.ThumbnailData

@Composable
fun FancyThumbnail(
    thumbnailData: ThumbnailData,
    modifier: Modifier = Modifier,
) {
    val (image, noThumbnailText) = thumbnailData
    BoxWithConstraints(
        modifier = Modifier.then(modifier)
    ) {
        Card(
            Modifier
                .fillMaxWidth()
                .height(maxWidth * 4 / 2)
        ) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                image?.let {
                    Image(
                        it.asImageBitmap(),
                        "thumbnail",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize()
                    )
                } ?: Box(
                    Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = noThumbnailText,
                        Modifier.fillMaxWidth(),
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
    }
}
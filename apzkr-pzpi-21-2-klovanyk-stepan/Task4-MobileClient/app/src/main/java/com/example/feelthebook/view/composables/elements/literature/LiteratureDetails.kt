package com.example.feelthebook.view.composables.elements.literature

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.feelthebook.models.basic.ThumbnailData
import com.example.feelthebook.models.retrofit.moshi.Literature

@Composable
fun LiteratureDetails(
    literature: Literature,
    thumbnailData: ThumbnailData,
    modifier: Modifier = Modifier,
) {
    Box(modifier = modifier) {
        LazyColumn(
            Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            item {
                Card(
                    Modifier
                ) {
                    FancyThumbnail(thumbnailData)
                }
            }
            item {
                Column(
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("Name: ${literature.name}${literature.minAge?.let { " ($it+)" } ?: ""}",
                        style = MaterialTheme.typography.titleLarge)
                    Text("Type: ${literature.literatureType.name}")
                    Text(
                        "Description: ${literature.description}",
                        style = MaterialTheme.typography.bodyLarge
                    )
                    Text(
                        "Pages: ${literature.pages}",
                        style = MaterialTheme.typography.bodyLarge
                    )
                    Text("Authors: ${
                        literature.authors.map {
                            "${it.pseudonym}${
                                listOf(
                                    it.name,
                                    it.surname
                                ).filterNotNull()
                                    .takeIf { it.isNotEmpty() }
                                    ?.joinToString(
                                        " ",
                                        " (",
                                        ")"
                                    ) ?: ""

                            }"
                        }
                            .joinToString(", ")
                    }")
                    Text("Genres: ${
                        literature.genres.map { it.name }
                            .joinToString(", ")
                    }")
                }
            }
        }
    }
}
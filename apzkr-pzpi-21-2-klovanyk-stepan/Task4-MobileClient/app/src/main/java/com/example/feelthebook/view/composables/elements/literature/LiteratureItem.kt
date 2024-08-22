package com.example.feelthebook.view.composables.elements.literature

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LocalMinimumInteractiveComponentEnforcement
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.feelthebook.models.basic.ThumbnailData
import com.example.feelthebook.models.retrofit.moshi.Literature
import kotlin.math.absoluteValue

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LiteratureItem(
    literature: Literature,
    thumbnailData: ThumbnailData,
    onDetailsClick: (Literature, ThumbnailData) -> Unit,
    onReadClick: ((Literature) -> Unit)?,
    modifier: Modifier = Modifier,
) {
    ElevatedCard(
        Modifier
            .aspectRatio(2f / 4.6f)
            .wrapContentSize()

    ) {
        Column(
            Modifier.padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ElevatedCard(Modifier.weight(1f)) {
                Column(
                    Modifier.padding(8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    FancyThumbnail(
                        thumbnailData,
                        Modifier.weight(1f)
                    )
                    Text(
                        literature.name,
                        style = MaterialTheme.typography.titleLarge
                    )
                }
            }
            Box(
                contentAlignment = Alignment.Center
            ) {
                ElevatedCard(
                    colors = CardDefaults.elevatedCardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Box(Modifier.padding(4.dp)) {
                        when (literature.genres.size) {
                            0 -> Text("No genres")
                            1 -> Text(literature.genres[0].name)
                            else -> Column(
                                Modifier.horizontalScroll(rememberScrollState()),
                                verticalArrangement = Arrangement.spacedBy(2.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                val lanes = mutableListOf<String>() to mutableListOf<String>()
                                literature.genres.forEach { genre ->
                                    lanes.toList()
                                        .map { it.sumOf { it.length } }
                                        .zipWithNext()
                                        .single()
                                        .apply {
                                            genre.name.length.let {
                                                (first + it - second).absoluteValue to (first - second + it).absoluteValue
                                            }
                                        }
                                        .run {
                                            when (first > second) {
                                                true -> lanes.second += genre.name
                                                false -> lanes.first += genre.name
                                            }
                                        }
                                }
                                lanes.toList()
                                    .map { genres ->
                                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                            genres.map { genre ->
                                                ElevatedCard {
                                                    Text(
                                                        genre,
                                                        Modifier.padding(4.dp)
                                                    )
                                                }
                                            }
                                        }
                                    }
                            }
                        }
                    }
                }
            }

            CompositionLocalProvider(
                LocalMinimumInteractiveComponentEnforcement provides false
            ) {
                Button(
                    onClick = {
                        onDetailsClick(
                            literature,
                            thumbnailData
                        )
                    },
                    Modifier.defaultMinSize(
                        1.dp,
                        1.dp
                    ),
                    contentPadding = PaddingValues(0.dp)
                ) {
                    Text(
                        "More",
                        Modifier.padding(
                            24.dp,
                            4.dp
                        )
                    )
                }
                if (onReadClick != null)
                    Button(
                        onClick = {
                            onReadClick(literature)
                        },
                        Modifier.defaultMinSize(
                            1.dp,
                            1.dp
                        ),
                        colors = ButtonDefaults.buttonColors(
                            contentColor = MaterialTheme.colorScheme.onTertiary,
                            containerColor = MaterialTheme.colorScheme.tertiary
                        ),
                        contentPadding = PaddingValues(0.dp)
                    ) {
                        Text(
                            "Read",
                            Modifier.padding(
                                24.dp,
                                4.dp
                            )
                        )
                    }
            }
        }
    }
}
package com.example.feelthebook.view.navigation.graphs

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import androidx.navigation.compose.navigation
import com.example.feelthebook.view.composables.elements.literature.LiteratureDetails
import com.example.feelthebook.LiteratureFetchingMode
import com.example.feelthebook.R
import com.example.feelthebook.models.navigation.NavDestinations
import com.example.feelthebook.models.retrofit.moshi.Configuration
import com.example.feelthebook.models.retrofit.moshi.LightDevice
import com.example.feelthebook.models.retrofit.moshi.PageConfig
import com.example.feelthebook.models.retrofit.moshi.ReadingLiterature
import com.example.feelthebook.models.retrofit.services.APILiteratureReadingService
import com.example.feelthebook.utils.emitErrorFromResponseFailure
import com.example.feelthebook.utils.retrofit.NavDestinationLabels
import com.example.feelthebook.view.composables.complex.LiteraturesComplex
import com.example.feelthebook.view.models.DetailsScreenViewModel
import com.tom_roush.pdfbox.cos.COSStream
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.pdmodel.PDPage
import com.tom_roush.pdfbox.pdmodel.font.FontMapper
import com.tom_roush.pdfbox.pdmodel.font.FontMappers
import com.tom_roush.pdfbox.pdmodel.font.PDFont
import com.tom_roush.pdfbox.pdmodel.font.PDType1Font
import com.tom_roush.pdfbox.rendering.PDFRenderer
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.last
import kotlinx.coroutines.launch
import kotlinx.coroutines.yield
import okhttp3.HttpUrl
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.POST
import javax.inject.Inject
import kotlin.math.abs
import kotlin.math.absoluteValue
import kotlin.math.roundToInt
import kotlin.math.sign

fun NavGraphBuilder.literaturesNavigationGraph(
    navController: NavHostController,
    onLabelChange: (String) -> Unit,
) {
    navigation<NavDestinations.Literatures>(
        startDestination = NavDestinations.Literatures.Collections
    ) {
        navigation<NavDestinations.Literatures.Collections>(
            startDestination = NavDestinations.Literatures.Collections.All
        ) {
            composable<NavDestinations.Literatures.Collections.All> {
                onLabelChange(NavDestinationLabels.All_Literatures.toString())
                LiteraturesComplex(
                    navBackStackEntry = it,
                    navController = navController,
                    fetchingMode = LiteratureFetchingMode.All,
                    null
                )
            }
            composable<NavDestinations.Literatures.Collections.Available> {
                onLabelChange(NavDestinationLabels.Available_Literatures.toString())
                val parentEntry = remember(it) {
                    navController.getBackStackEntry(NavDestinations.Literatures)
                }
                val readerViewModel: ReaderViewModel = hiltViewModel(parentEntry)
                LiteraturesComplex(
                    navBackStackEntry = it,
                    navController = navController,
                    fetchingMode = LiteratureFetchingMode.Available,
                    onReadClick = {
                        readerViewModel.viewModelScope.launch {
                            readerViewModel.loadReadingData(it.id)
                        }
                        navController.navigate(NavDestinations.Literatures.Reader)
                    }
                )
            }

        }
    }
    composable<NavDestinations.Literatures.Details> {
        onLabelChange(NavDestinationLabels.Literatures_Details.toString())
        Box(
            Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            val parentEntry = remember(it) {
                navController.getBackStackEntry(NavDestinations.Literatures)
            }
            val detailsScreenViewModel: DetailsScreenViewModel = hiltViewModel(parentEntry)
            val details by detailsScreenViewModel.detailsLiterature.collectAsState()

            details?.let { (literature, thumbnailData) ->
                LiteratureDetails(
                    literature = literature,
                    thumbnailData = thumbnailData
                )
            }
        }
    }
    composable<NavDestinations.Literatures.Reader> {
        onLabelChange(NavDestinationLabels.Reader.toString())
        Box(
            Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            val parentEntry = remember(it) {
                navController.getBackStackEntry(NavDestinations.Literatures)
            }
            val readerViewModel: ReaderViewModel = hiltViewModel(parentEntry)
            val pdfBitmaps by readerViewModel.pdfBitmaps.collectAsState()
            //            val exitTrigger by readerViewModel.readerExitTrigger.collectAsState()
            //
            //            LaunchedEffect(exitTrigger) {
            //                if (exitTrigger > 0) {
            //                    readerViewModel.resetExitTrigger()
            //                    navController.popBackStack()
            //                }
            //            }

            LiteratureReader(
                pagesData = pdfBitmaps ?: emptyList(),
                onPageChanged = {
                    Log.d("testpagechange", it.toString())
                    readerViewModel.syncIoTDevicesWithConfigs(it)
                },
                onLeave = {
                    readerViewModel.offIoT()
                }
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun PreviewLiteratureReader() {
    Box(Modifier.fillMaxSize()) {
        val resources = LocalContext.current.resources
        LiteratureReader(
            pagesData = Array(7) {
                it to BitmapFactory.decodeResource(
                    resources,
                    R.drawable.cbc84b919037eug55n14q
                )
            }.toList(),
            onPageChanged = {},
            onLeave = {}
        )
    }
}

@Composable
fun LiteratureReader(
    pagesData: List<Pair<Int, Bitmap>>,
    onPageChanged: (visiblePages: List<Int>) -> Unit,
    onLeave: () -> Unit
) {
    val state = rememberLazyListState()
    val pageNum by remember {
        derivedStateOf {
            state.layoutInfo.visibleItemsInfo.map { (it.key as Int) + 1 }
                .average().takeIf { !it.isNaN() }?.roundToInt()?: 0
        }
    }

    DisposableEffect(true) {
        onDispose {
            onLeave()
        }
    }

    LaunchedEffect(state) {
        Log.d("PAGEIOTLOG", "Any changes detected")
        snapshotFlow { state.layoutInfo.visibleItemsInfo }
            .debounce(1000)
            .distinctUntilChanged { old, new ->
                old.map { it.key as Int }
                    .sorted() == new.map { it.key as Int }
                    .sorted()
            }
            .collect {
                Log.d("PAGEIOTLOG", "Pages: ${it.map { (it.key as Int) + 1 }}")
                onPageChanged(it.map { (it.key as Int) + 1 })
            }
    }

    Column {
        LazyColumn(
            Modifier
                .fillMaxWidth()
                .weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally,
            contentPadding = PaddingValues(8.dp),
            verticalArrangement = Arrangement.spacedBy(2.dp),
            state = state
        ) {
            items(pagesData, key = { it.first }) {
                Image(
                    it.second.asImageBitmap(), it.first.toString(),
                    modifier = Modifier.fillMaxWidth(),
                    contentScale = ContentScale.FillWidth,
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            Text(text = pageNum.toString())
        }
    }

}

@HiltViewModel
class ReaderViewModel @Inject constructor(
    private val apiLiteratureReadingService: APILiteratureReadingService,
    private val retrofitBuilder: Retrofit.Builder,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    private var _readableLiterature: MutableStateFlow<ReadingLiterature?> = MutableStateFlow(null)
    private var _pdfAsBitmaps: MutableStateFlow<List<Pair<Int, Bitmap>>?> = MutableStateFlow(null)
    private var _destinationDevices: MutableStateFlow<List<LightDevice>?> = MutableStateFlow(null)
    private var hub: IoTHub? = null

    private var _readerExitTrigger: MutableStateFlow<Int> = MutableStateFlow(0)
    val readerExitTrigger = _readerExitTrigger.asStateFlow()

    val pdfBitmaps = _pdfAsBitmaps.asStateFlow()

    suspend fun loadReadingData(literatureId: Int) {
        _readableLiterature.value = null
        _pdfAsBitmaps.value = null
        _destinationDevices.value = null
        _readerExitTrigger.value = 0

        _destinationDevices.emit(fetchDestinationDevices())
        _readableLiterature.emit(fetchLiterature(literatureId))
        fetchPdfAsBitmaps(literatureId)
    }

    suspend fun resetExitTrigger() {
        _readerExitTrigger.emit(0)
    }

    private suspend fun fetchDestinationDevices(): List<LightDevice>? =
        with(apiLiteratureReadingService.getFirstAvailableLightDevices()) {
            if (isSuccessful) return body()!!.also {
                hub = IoTHub(
                    it,
                    retrofitBuilder,
                    context
                )
            }
            else run {
                emitErrorFromResponseFailure("Failed to get light devices")
                    .run {
                        if (contains("NO_BOOKINGS_AVAILABLE"))
                            _readerExitTrigger.emit(_readerExitTrigger.value + 1)
                    }

            }.let { null }
        }

    fun offIoT() = viewModelScope.launch{
        hub?.sendConfigurations(
            mapOf("Sun" to Configuration(0, null, null))
        )
    }

    fun syncIoTDevicesWithConfigs(pages: List<Int>) =
        viewModelScope.launch {
            Log.d("SyncCheck", "Syncing")
            val configs = _readableLiterature.value?.pageConfigs ?: return@launch
            val orderedPages = smartPagesOrder(pages)
            orderedPages.firstNotNullOfOrNull { pageNum ->
                configs.filter { it.pageNumber == pageNum }
                    .takeIf { it.isNotEmpty() }
            }
                ?.groupBy { it.lightTypeName }
                ?.mapValues { (_, pageConfig) ->
                    pageConfig.map { it.configuration }
                        .first()
                }
                ?.run {
                    Log.d("synciot", this.toString())
                    hub?.sendConfigurations(this)
                }
        }

    private fun smartPagesOrder(pages: List<Int>) =
        pages.withIndex()
            .sortedBy {
                (it.index - pages.size.toFloat() / 2).let { abs(it) + it.sign * 0.5 }
            }
            .map { it.value }

    private suspend fun fetchLiterature(literatureId: Int): ReadingLiterature? =
        with(apiLiteratureReadingService.getReadingLiterature(literatureId)) {
            if (isSuccessful) return body()!!.also { Log.d("litcheck", it.toString()) }
            else run { emitErrorFromResponseFailure("Failed to get literature") }.let { null }
        }


    private suspend fun fetchPdfAsBitmaps(literatureId: Int) =
        fetchPdf(literatureId)?.let {
            val channel = pdfToBitmaps(it)
            for (bitmapIndexed in channel) (_pdfAsBitmaps.value ?: listOf()).run {
                _pdfAsBitmaps.emit(plus(bitmapIndexed))
                Log.d("PDFBox", "Page ${bitmapIndexed.first} added")
            }
        }

    private suspend fun fetchPdf(literatureId: Int): ResponseBody? =
        with(apiLiteratureReadingService.getLiteraturePDF(literatureId)) {
            if (isSuccessful) return body()!!
            else run { emitErrorFromResponseFailure("Failed to get pdf") }.let { null }
        }

    private suspend fun pdfToBitmaps(rawBody: ResponseBody): Channel<Pair<Int, Bitmap>> {
        val channel = Channel<Pair<Int, Bitmap>>(Channel.UNLIMITED)
        viewModelScope.launch(Dispatchers.IO) {
            rawBody.byteStream()
                .let { stream -> PDDocument.load(stream) }
                .let { document ->
                    document to PDFRenderer(document)
                }
                .let { (document, renderer) ->
                    for (pageIndex in 0 until document.numberOfPages) {
                        Log.d("PDFBox", "Page $pageIndex rendering...")
                        val image = renderer.renderImage(pageIndex, 2.0f)
                        Log.d("PDFBox", "Page $pageIndex rendered")
                        channel.send(pageIndex to image)
                    }
                    channel.close()
                }
        }
        return channel

    }
}

class IoTHub(
    deviceData: List<LightDevice>,
    retrofitBuilder: Retrofit.Builder,
    context: Context,
) {
    private val services = deviceData
        .groupBy { it.lightTypeName }
        .map { (typeName, devices) ->
            typeName to (devices
                .map {
                    "${
                        ContextCompat.getString(
                            context,
                            R.string.iot_scheme
                        )
                    }${it.host}:${it.port}"
                }
                .map {
                    retrofitBuilder.baseUrl(it)
                        .build()
                        .create(IoTService::class.java)
                }
                    )
        }
        .toMap()

    suspend fun sendConfigurations(configs: Map<String, Configuration>) {
        configs.forEach { (typeName, config) ->
            services[typeName]?.forEach {
                it.postConfigToIot(config)
                Log.d("iot_setup", "Config sent: $config")
            }
        }
    }
}

interface IoTService {
    @POST("/")
    suspend fun postConfigToIot(
        @Body config: Configuration,
    )
}


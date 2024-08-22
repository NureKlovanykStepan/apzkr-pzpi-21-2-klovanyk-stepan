from app.database.models import Literature
from app.services.route_exstensions.literatures.implementations import (LiteratureRootDestroyingDetailsImpl, \
                                                                        LiteratureThumbnailPostingImpl,
                                                                        LiteraturePdfPostingImpl,
                                                                        LiteratureThumbnailGettingImpl,
                                                                        LiteraturePdfGettingImpl, \
                                                                        LiteratureDropGenresDetailsImpl,
                                                                        LiteratureDropAuthorsDetailsImpl,
                                                                        LiteratureFullyReadableDetailsImpl,
                                                                        LiteratureFullyEditableDetailsImpl)
from app.services.route_exstensions.literatures.validators_additions import (entryEdit_userOnly,
                                                                             entryEdit_forPdfReading, \
                                                                             entryEdit_forEditing,
                                                                             multi_genre_filtering_query_mod)
from app.utils.extra import DefaultExtraValidators
from app.services.creators.builders.buieprints import BlueprintDefaults
from app.services.decorators.general.permissions import RequiredPermissionsFlag as Perm

registered = (
    BlueprintDefaults("literatures", Literature, DefaultExtraValidators)
    .default()
    # access - info only
    .useDefault_ReadSingleRequest()
    .useDefault_ReadManyRequest(multi_genre_filtering_query_mod)

    .route_Builder().var("id").cat("thumbnail").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureThumbnailGettingImpl)
    # access - info and can read (pdf)
    .extraValidators_SnapshotStorage()

    .route_Builder().cat("available").build()
    .edit_ValidationStorageEntry(entryEdit_userOnly)
    .buildRequest_onBodyFactoryAdvanced(LiteratureFullyReadableDetailsImpl)
    .route_Builder().var("id").cat("pdf").build()

    .extraValidators_RestoreLiveStorage()
    .extraValidators_SnapshotStorage()

    .route_Builder().var("id").cat("pdf").build()
    .edit_ValidationStorageEntry(entryEdit_forPdfReading)
    .buildRequest_onBodyFactoryAdvanced(LiteraturePdfGettingImpl)

    .extraValidators_RestoreLiveStorage()
    # access - edit
    .permissions_Set(Perm.LITERATURE_MANAGER)

    .route_Builder().cat("editable").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureFullyEditableDetailsImpl)

    .extraValidators_SnapshotStorage()

    .edit_ValidationStorageEntry(entryEdit_forEditing)
    .useDefault_CreateRequest()
    .useDefault_DeleteRequest()
    .useDefault_UpdateRequest()

    .route_Builder().var("id").cat("drop_genres").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureDropGenresDetailsImpl)
    .route_Builder().var("id").cat("drop_authors").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureDropAuthorsDetailsImpl)
    .route_Builder().var("id").cat("drop_root_content").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureRootDestroyingDetailsImpl)

    .route_Builder().var("id").cat("pdf").build()
    .buildRequest_onBodyFactoryAdvanced(LiteraturePdfPostingImpl)
    .route_Builder().var("id").cat("thumbnail").build()
    .buildRequest_onBodyFactoryAdvanced(LiteratureThumbnailPostingImpl)

    .extraValidators_RestoreLiveStorage()
)

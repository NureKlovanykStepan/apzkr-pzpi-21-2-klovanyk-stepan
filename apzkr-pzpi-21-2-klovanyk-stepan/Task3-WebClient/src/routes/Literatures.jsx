import React, {useState, useRef, useEffect, useMemo} from 'react';
import {Document, Page, pdfjs, DocumentCallback} from 'react-pdf';
import {API} from "../App";
import Literature from "../models/Literature";
import "../styles/Literatures.css"
import {Buffer} from "buffer";
import Select from "react-select";
import CreatableSelect from "react-select/creatable";
import Author from "../models/Author";
import {useResizeDetector} from "react-resize-detector";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url
).toString();

const DISABLE_THUMBNAIL_LOADING = false

export default function Literatures({
                                        employee, company
                                    })
{
    const [availableLiteratures, setAvailableLiteratures] = useState(/** @type {Literature[]}*/
        []);
    const [selectedLiterature, setSelectedLiterature] = useState(null);
    const [availableLiteraturesThumbnails, setAvailableLiteraturesThumbnails] = useState(/** @type {{[literature_id: int]: Blob}}*/
        {});
    const [isEditorCreateMode, setIsEditorCreateMode] = useState(false);

    const loadLiteratures = async () => {
        await API.get('/literatures/editable?I=literature,employee,user,genre,literature_type,author')
            .then((response) => {
                setAvailableLiteratures(response.data.map(literature => new Literature(literature)));
            })
            .catch(error => {
                window.alert(error.response?.data ?? error)
            })
    }

    useEffect(
        () => {
            setAvailableLiteraturesThumbnails({})
            setSelectedLiterature(null)
            if (!company) return
            loadLiteratures()
        },
        [company]
    )

    useEffect(
        () => {
            availableLiteratures.forEach(async literature => {
                if (DISABLE_THUMBNAIL_LOADING) return
                if (availableLiteraturesThumbnails[literature.id]) return
                const thumbnail =
                    literature.thumbnail_PATH === null
                        ? null
                        : await API.get(
                            `/literatures/${literature.id}/thumbnail?width=300`,
                            {responseType: 'blob'}
                        )
                            .then(response => response.data)
                            .catch(async error => {
                                const response_text = await error.response?.data?.text()
                                if (!response_text) throw error
                                if (response_text.includes("ERROR_TYPE: RESOURCE_NOT_FOUND")) return null
                                throw error
                            })
                            .catch(ignore => null)

                setAvailableLiteraturesThumbnails(prev => (
                    {
                        ...prev, [literature.id]: thumbnail
                    }
                ))
            })
        },
        [availableLiteratures]
    )

    const handleDelete = async (literature) => {
        await API.delete(`/literatures/${literature.id}`)
            .then(() => {
                if (selectedLiterature?.id === literature.id) {
                    setSelectedLiterature(null)
                    setAvailableLiteraturesThumbnails({})

                }
                loadLiteratures()
            })
            .catch(error => {
                window.alert(error.response?.data ?? error)
            })
    }

    return (
        <div className="literatures container">
            {!selectedLiterature
                ? <div className="literatures create-new">
                    <button
                        onClick={() => {
                            setIsEditorCreateMode(true)
                            setSelectedLiterature(new Literature({}))
                        }}
                    >Create new
                    </button>
                </div>
                : <LiteratureEditor literature={selectedLiterature}
                                    employee={employee}
                                    company={company}
                                    onLiteratureUpdated={(literature) => {
                                        setSelectedLiterature(null)
                                        const shallowThumbnails = {...availableLiteraturesThumbnails}
                                        delete shallowThumbnails[literature.id]
                                        setAvailableLiteraturesThumbnails(shallowThumbnails)
                                        loadLiteratures()
                                    }}
                                    onEditorClose={() => {
                                        setSelectedLiterature(null)
                                    }}
                                    isCreate={isEditorCreateMode}
                />}
            {availableLiteratures.length > 0
                ? <div className="literatures literatures-list grid">
                    {availableLiteratures.map(literature => (
                        <div key={literature.id}
                             className="literatures literatures-list item item-container"
                        >
                            <div className="item image-container">
                                {(
                                    () => {
                                        if (!availableLiteraturesThumbnails.hasOwnProperty(literature.id)) return <img
                                            alt={"Thumbnail loading..."}
                                        />
                                        const thumbnail_blob = availableLiteraturesThumbnails[literature.id]
                                        if (!thumbnail_blob) return <img alt={"No thumbnail"}/>
                                        return <img
                                            alt={`${literature.name}_thumbnail`}
                                            src={URL.createObjectURL(thumbnail_blob)}
                                        />
                                    }
                                )()}
                            </div>
                            <div className="literatures-list item info-container">
                                <p>{literature.name}</p>
                            </div>
                            <div className="literatures-list item actions-container">
                                <button
                                    className="literatures-list action edit"
                                    onClick={() => {
                                        setIsEditorCreateMode(false)
                                        setSelectedLiterature(literature)
                                    }}
                                >Edit
                                </button>
                                <button
                                    onClick={() => handleDelete(literature)}
                                >Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
                : <h3>No available literatures</h3>}
        </div>
    );
}

/**
 *
 * @param {Literature} literature
 * @param {Employee} employee
 * @param {Company} company
 * @param {(literature: Literature) => void} onLiteratureUpdated
 * @param {boolean} isCreate
 * @param {() => void} onEditorClose
 * @returns {Element}
 * @constructor
 */
function LiteratureEditor({literature, employee, company, onLiteratureUpdated, onEditorClose, isCreate}) {
    const [complexData, setComplexData] = useState(/** @type {{thumbnail: Blob, pdf: Blob, mutableLiterature: Literature}}*/
        null);
    const [mutableLiterature, setMutableLiterature] = useState(/** @type {Literature}*/
        null);
    const [isLoading, setIsLoading] = useState(false);
    const [availableGenres, setAvailableGenres] = useState(/** @type {{name: string}[]}*/
        [])
    const [availableAuthors, setAvailableAuthors] = useState(/** @type {Author[]}*/
        [])
    const [availableTypes, setAvailableTypes] = useState(/** @type {{name: string}[]}*/
        [])

    const loadPdf = async (mutableLiterature) => {
        return !mutableLiterature.id
            ? null
            : await API.get(
                `/literatures/${mutableLiterature.id}/pdf`,
                {responseType: 'blob'}
            )
                .then(response => {
                    console.log(123);
                    return response
                })
                .then((response) => response.data)
                .catch(async error => {
                    const response_text = await error.response?.data?.text()
                    if (!response_text) throw error
                    if (response_text.includes("ERROR_TYPE: RESOURCE_NOT_FOUND")) return null
                    window.alert(response_text)
                })
    }
    const loadThumbnail = async (mutableLiterature) => {
        return !mutableLiterature.id
            ? null
            : await API.get(
                `/literatures/${mutableLiterature.id}/thumbnail`,
                {responseType: 'blob'}
            )
                .then(response => response.data)
                .catch(async error => {
                    const response_text = await error.response?.data?.text()
                    if (!response_text) throw error
                    if (response_text.includes("ERROR_TYPE: RESOURCE_NOT_FOUND")) return null
                    window.alert(response_text)
                })
    }
    const loadAvailableGenres = async () => {
        await API.get('/genres?I=genre')
            .then(response => setAvailableGenres(response.data))
            .catch(error => window.alert(error.response?.data ?? error))
    }
    const loadAvailableAuthors = async () => {
        await API.get('/authors?I=author')
            .then(response => setAvailableAuthors(response.data.map(author => new Author(author))))
            .catch(error => window.alert(error.response?.data ?? error))
    }
    const loadAvailableTypes = async () => {
        await API.get('/literature_types?I=literature_type')
            .then(response => setAvailableTypes(response.data))
            .catch(error => window.alert(error.response?.data ?? error))
    }
    useEffect(
        () => {
            const mutableLiterature = new Literature({
                ...literature, pages: null,
            })
            setIsLoading(true)
            setMutableLiterature(null)
            loadPdf(mutableLiterature)
                .then(pdf => {
                    loadThumbnail(mutableLiterature)
                        .then(thumbnail => setComplexData({
                            thumbnail: thumbnail, pdf: pdf, mutableLiterature: mutableLiterature
                        }))
                })

        },
        [literature]
    )

    useEffect(
        () => {
            if (!complexData) return
            setMutableLiterature(complexData.mutableLiterature)
            setIsLoading(false)
        },
        [complexData]
    )

    useEffect(
        () => {
            loadAvailableGenres()
            loadAvailableAuthors()
            loadAvailableTypes()
        },
        []
    );

    /**
     *
     * @param {{mutableLiterature: Literature, employee: Employee, company: Company}}data
     * @returns {{type_name, pages, pdf_PATH: null, thumbnail_PATH: null, company_id, name, description, min_age, editor_email}}
     */
    const createFilteredLiteratureData = (data) => {
        return {
            name: data.mutableLiterature.name, description: data.mutableLiterature.description,
            pages: data.mutableLiterature.pages, min_age: data.mutableLiterature.min_age,
            editor_email: data.employee.user_email, company_id: data.company.id, pdf_PATH: null, thumbnail_PATH: null,
            type_name: data.mutableLiterature.type_name
        }

    }

    /**
     *
     * @param {{mutableLiterature: Literature, employee: Employee, company: Company}} data
     * @returns {Promise<{success_message: string, pk_data: {}}>}
     */
    const updateWithData = async (data) => {
        return await API.put(
            `/literatures/${data.mutableLiterature.id}`,
            createFilteredLiteratureData(data)
        )
            .then(response => response.data)
    }

    /**
     *
     * @param {{mutableLiterature: Literature, employee: Employee, company: Company}} data
     * @returns {Promise<{success_message: string, pk_data: {}}>}
     */
    const createWithData = async (data) => {
        return await API.post(
            '/literatures/',
            createFilteredLiteratureData(data)
        )
            .then(response => response.data)
    }

    /**
     *
     * @param {{mutableLiterature: Literature}} data
     * @returns {Promise<void>}
     */
    const dropLiteratureFiles = async (data) => {
        return await API.delete(`/literatures/${data.mutableLiterature.id}/drop_root_content`)
    }

    const formWithFileData = (
        form,
        data
    ) => {
        form.append(
            "file",
            data
        )
        return form
    }

    /**
     *
     * @param {{pdf: Blob, mutableLiterature: Literature}} data
     * @returns {Promise<void>}
     */
    const uploadPdf = async (data) => {
        if (data.pdf) await API.post(
            `/literatures/${data.mutableLiterature.id}/pdf`,
            formWithFileData(
                new FormData(),
                new File(
                    [data.pdf],
                    data.pdf.name ?? "literature.pdf",
                    {
                        type: "application/pdf"
                    }
                )
            ),
        )
    }

    /**
     *
     * @param {{thumbnail: Blob, mutableLiterature: Literature}} data
     * @returns {Promise<void>}
     */
    const uploadThumbnail = async (data) => {
        if (data.thumbnail) await API.post(
            `/literatures/${data.mutableLiterature.id}/thumbnail`,
            formWithFileData(
                new FormData(),
                new File(
                    [data.thumbnail],
                    data.thumbnail.name ?? "literature.png",
                    {
                        type: "image/png"
                    }
                )
            ),
        )
    }
    /**
     *
     * @param {{mutableLiterature: Literature}} data
     * @returns {Promise<void>}
     */
    const updateGenres = async (data) => {
        await API.delete(`/literatures/${data.mutableLiterature.id}/drop_genres`)
            .then(() => {
                data.mutableLiterature.genres.forEach(async currentGenre => {
                    const postCrossRef = async () => (
                        await API.post(
                            `/literature_genre_x/`,
                            {
                                genre_name: currentGenre.name, literature_id: data.mutableLiterature.id
                            }
                        )
                            .catch(error => window.alert(error.response?.data ?? error))
                    )
                    if (availableGenres.find(genre => genre.name === currentGenre.name)) { await postCrossRef() } else {
                        await API.post(
                            `/genres/`,
                            currentGenre
                        )
                            .then(async () => await postCrossRef())
                            .catch(error => window.alert(error.response?.data ?? error))
                    }
                })
            })
    }

    const updateAuthors = async (data) => {
        await API.delete(`/literatures/${data.mutableLiterature.id}/drop_authors`)
            .then(() => {
                data.mutableLiterature.authors.forEach(async currentAuthor => {
                    const postCrossRef = async (author_id) => (
                        await API.post(
                            `/literature_author_x/`,
                            {
                                author_id: author_id, literature_id: data.mutableLiterature.id
                            }
                        )
                            .catch(error => window.alert(error.response?.data ?? error))
                    )
                    const foundAuthor = availableAuthors.find(author => author.equalsTo(currentAuthor))
                    if (foundAuthor) { await postCrossRef(foundAuthor.id) } else {
                        await API.post(
                            `/authors/`,
                            currentAuthor
                        )
                            .then(async (response) => await postCrossRef(response.data.pk_data.id))
                            .catch(error => window.alert(error.response?.data ?? error))
                    }
                })
            })
    }

    /**
     *
     * @param {{mutableLiterature: Literature}} data
     * @returns {Promise<void>}
     */
    const updateType = async (data) => {
        const putType = async () => (
            await API.put(
                `/literatures/${data.mutableLiterature.id}`,
                {
                    type_name: data.mutableLiterature.type_name
                }
            )
                .catch(error => window.alert(error.response?.data ?? error))
        )
        const createTypeOrPass = async () => {
            if (!availableTypes.find(type => type.name === data.mutableLiterature.type_name)) {
                await API.post(
                    `/literature_types/`,
                    {
                        name: data.mutableLiterature.type_name
                    }
                )
                    .catch(error => window.alert(error.response?.data ?? error))
            }
        }
        await createTypeOrPass()
            .then(async () => await putType())

    }
    const handleSave = async () => {
        if (!mutableLiterature) return
        const frozenData = {
            ...complexData, mutableLiterature: mutableLiterature, company: company, employee: employee
        }
        const initializerMethod = isCreate
            ? createWithData
            : updateWithData
        await initializerMethod(frozenData)
            .then(response => frozenData.mutableLiterature.id = response.pk_data.id)
            .then(async () => await updateGenres(frozenData))
            .then(async () => await updateAuthors(frozenData))
            .then(async () => await updateType(frozenData))
            .then(async () => await dropLiteratureFiles(frozenData)
                .then(async () => {
                    await uploadPdf(frozenData)
                        .catch(error => window.alert(`PDF upload error\n${error.response?.data ?? error}`))
                    await uploadThumbnail(frozenData)
                        .catch(error => window.alert(`Thumbnail upload error\n${error.response?.data ?? error}`))
                })
                .then(() => {
                    window.alert("Updated successfully")
                    onLiteratureUpdated(frozenData.mutableLiterature)
                }))
            .catch(error => window.alert(error.response?.data ?? error))
    }

    const {width, ref: pdfPreviewDiv} = useResizeDetector()


    return !mutableLiterature
        ? (
            !isLoading
                ? null
                : <p>Editor Loading...</p>
        )
        : (
            <div className="literature-editor container">
                <div className="details-row">
                    <div className="pdf-container">
                        <div ref={pdfPreviewDiv}
                             className="pdf-preview">
                            <Document className="document"
                                      file={complexData.pdf}
                                      onLoadSuccess={async callback => {
                                          const currentData = await callback.getData()
                                          const latestData = new Uint8Array(await complexData.pdf.arrayBuffer())
                                          if (Buffer.from(currentData)
                                                  .equals(Buffer.from(latestData)) && mutableLiterature
                                              === complexData.mutableLiterature)
                                          {
                                              setMutableLiterature({
                                                  ...mutableLiterature, pages: callback.numPages
                                              })
                                          }
                                      }}>
                                {[...Array(mutableLiterature.pages)]
                                    .map((
                                        _,
                                        index
                                    ) => (
                                        <Page renderAnnotationLayer={false}
                                              renderTextLayer={false}
                                              width={width}
                                              pageNumber={index + 1}
                                              key={index}
                                        />
                                    ))}
                            </Document>
                        </div>
                        <div className="pdf-download">
                            <a
                                href={complexData.pdf
                                    ? URL.createObjectURL(complexData.pdf)
                                    : null}
                                download>
                                Download pdf
                            </a>
                        </div>
                        <div className="pdf-setup">
                            <input
                                type="file"
                                accept=".pdf"
                                onChange={e => setComplexData({
                                    ...complexData, pdf: e.target.files[0], mutableLiterature: mutableLiterature
                                })}/>
                        </div>
                    </div>
                    <div className="thumbnail-container">
                        <div className="thumbnail-preview">
                            <img alt={"No thumbnail"}
                                 src={complexData.thumbnail
                                     ? URL.createObjectURL(complexData.thumbnail)
                                     : null}/>
                        </div>
                        <div className="thumbnail-download">
                            <a
                                href={complexData.thumbnail
                                    ? URL.createObjectURL(complexData.thumbnail)
                                    : null}
                                download>
                                Download thumbnail
                            </a>
                        </div>
                        <div className="thumbnail-setup">
                            <input
                                type="file"
                                accept="image/*"
                                onChange={e => setComplexData({
                                    ...complexData, thumbnail: e.target.files[0], mutableLiterature: mutableLiterature
                                })}/>
                        </div>
                    </div>
                </div>
                <div className="attributes-container">
                    <label>Label: <input
                        onChange={e => setMutableLiterature({...mutableLiterature, name: e.target.value})}
                        value={mutableLiterature.name}
                        type="text"
                        placeholder="Enter label"/></label>
                    <p>Description: <textarea onChange={e => setMutableLiterature({
                        ...mutableLiterature, description: e.target.value
                    })}
                                              value={mutableLiterature.description}/></p>
                    <p>Pages: {mutableLiterature.pages}</p>
                    <label>Min Age: <input
                        onChange={e => setMutableLiterature({...mutableLiterature, min_age: e.target.value})}
                        value={mutableLiterature.min_age}
                        type="number"
                        placeholder="Not specified"/></label>
                    <p>Editor: {!mutableLiterature.editor_email
                        ? `[missing]`
                        : `${mutableLiterature.editor_email} [${(
                            ({
                                 real_name, real_surname
                             }) => `${real_name} ${real_surname}`
                        )(mutableLiterature.editor.user)}`}]</p>
                    <p>Genres:
                        <CreatableSelect
                            isMulti={true}
                            value={mutableLiterature.genres?.map(({name}) => new Option(
                                name,
                                name
                            )) ?? []}
                            onChange={data => setMutableLiterature({
                                ...mutableLiterature, genres: data?.map(({value}) => (
                                    {name: value}
                                )) ?? []
                            })}
                            options={availableGenres.map(({name}) => new Option(
                                name,
                                name
                            ))}/>
                    </p>
                    <p>Authors:
                        <CreatableSelect
                            isMulti={true}
                            options={availableAuthors.map(author => new Option(
                                author.toString(),
                                author.toString()
                            ))}
                            value={mutableLiterature.authors?.map(author => new Option(
                                author.toString(),
                                author.toString()
                            )) ?? []}
                            onChange={e => setMutableLiterature({
                                ...mutableLiterature, authors: e?.map(data => Author.fromString(data.value)) ?? []
                            })}
                            formatCreateLabel={(input) => `New author will be: ${[input].map(input => Author.fromString(input)
                                .toString())[0]}`}/>
                    </p>
                    <p>Type:
                        <CreatableSelect
                            options={availableTypes.map(({name}) => new Option(
                                name,
                                name
                            ))}
                            value={!mutableLiterature.type_name
                                ? null
                                : new Option(
                                    mutableLiterature.type_name,
                                    mutableLiterature.type_name
                                )}
                            onChange={e => setMutableLiterature({
                                ...mutableLiterature, type_name: e.value
                            })}/>
                    </p>
                </div>
                <div className="actions">
                    <button onClick={handleSave}
                            className="save-button">Save
                    </button>
                    <button
                        onClick={onEditorClose}>Close editor
                    </button>
                </div>
                {!complexData.pdf
                    ? null
                    : <PageConfigEditor literature={mutableLiterature}/>}
            </div>

        );
}

function PageConfigEditor({literature}) {
    const [availablePageConfigs, setAvailablePageConfigs] = useState(/** @type {{
         id: int,
         literature_id: int,
         page_number: int,
         light_type_name: string,
         configuration: {
         color: int,
         color_alter: int | null,
         color_alter_ms_delta: int | null,
         }
         }[]}*/
        [])
    const [availableLightTypes, setAvailableLightTypes] = useState(/** @type {{
         name: string,
         }[]}*/
        [])

    const availableGuidelines = Object.seal({
        SINGLE: Symbol("Single color"), DOUBLE: Symbol("Two colors within time delta")
    })

    const loadLightTypes = async () => {
        await API.get('/light_types/?I=light_type')
            .then((response) => {
                setAvailableLightTypes(response.data.map(light_type => (
                    {name: light_type.name}
                )));
            })
            .catch(error => {
                window.alert(error.response?.data ?? error)
            })
    }

    const loadLightConfigs = async () => {
        console.log('test')
        await API.get(`/literature_page_configs/for_literature/${literature.id}?I=literature_page_config`)
            .then(response => setAvailablePageConfigs(response.data))
            .catch(error => window.alert(error.response?.data ?? error))
    }

    useEffect(
        () => {
            loadLightConfigs()
            loadLightTypes()
        },
        [literature]
    )

    const infuseWithLiteratureId = (data) => {
        return {
            ...data, literature_id: literature.id
        }
    }

    const handlePageConfigCreation = async (data) => {
        await API.post(
            `/literature_page_configs/`,
            data
        )
            .then(response => window.alert(response.data.success_message))
            .then(() => loadLightConfigs())
            .then(() => updateCreationRow())
            .catch(error => window.alert(error.response?.data ?? error))
    }

    const handlePageConfigUpdate = async (data) => {
        await API.put(
            `/literature_page_configs/${data.id}`,
            data
        )
            .then(response => window.alert(response.data.success_message))
            .then(() => loadLightConfigs())
            .catch(error => window.alert(error.response?.data ?? error))
    }

    const handlePageConfigDeletion = async (id) => {
        await API.delete(`/literature_page_configs/${id}`)
            .then(response => window.alert(response.data.success_message))
            .then(() => loadLightConfigs())
            .catch(error => window.alert(error.response?.data ?? error))
    }

    const [creationRowUpdateTrigger, setCreationRowUpdateTrigger] = useState(0)
    const updateCreationRow = () => setCreationRowUpdateTrigger(creationRowUpdateTrigger + 1)
    return (
        <div className="page-configs-editor container">
            {!literature.pages
                ? <p>No pages</p>
                : <table>
                    <thead>
                    <tr>
                        <th>Page number</th>
                        <th>Light type</th>
                        <th>Config setup</th>
                        <th>Actions</th>
                    </tr>
                    </thead>
                    <tbody>
                    <React.Fragment key={creationRowUpdateTrigger}>
                        <PageConfigRow
                            constants={{
                                pagesCount: literature.pages, availableLightTypes: availableLightTypes,
                                availableGuidelines: availableGuidelines
                            }}
                            initialData={creationRowUpdateTrigger
                                ? null
                                : null}
                            key={"create-row"}
                            onDataSubmit={data => handlePageConfigCreation(infuseWithLiteratureId(data))}/>
                    </React.Fragment>
                    {availablePageConfigs.map(pageConfig => <PageConfigRow
                        constants={{
                            pagesCount: literature.pages, availableLightTypes: availableLightTypes,
                            availableGuidelines: availableGuidelines
                        }}
                        initialData={{...pageConfig, page: pageConfig.page_number}}
                        key={`edit-row-${pageConfig.id}`}
                        onDelete={(data) => handlePageConfigDeletion(pageConfig.id)}
                        onDataSubmit={data => handlePageConfigUpdate(infuseWithLiteratureId({
                            ...data, id: pageConfig.id
                        }))}
                    />)}
                    </tbody>
                </table>}
        </div>
    )
}

/**
 * @typedef {Object} LightDeviceConfiguration
 * @property {int} color
 * @property {int | null} color_alter
 * @property {int | null} color_alter_ms_delta
 */

/**
 *
 * @param {{
 *     pagesCount: int,
 *     availableLightTypes: {name: string}[],
 *     availableGuidelines: {[key: string]: symbol}
 * }} constants
 * @param {{
 *    page: int,
 *    light_type_name: string,
 *    configuration: LightDeviceConfiguration
 * } | null} initialData
 * @param {
 *     ({
 *         page_number: int,
 *         light_type_name: string,
 *         configuration: LightDeviceConfiguration
 *     }) => void
 * } onDataSubmit
 * @param {() => void} onDelete
 * @param {string} key
 * @returns {Element}
 * @constructor
 */
function PageConfigRow({constants, initialData, onDataSubmit, onDelete, key}) {
    const [selectedPage, setSelectedPage] = useState(initialData?.page);
    const [selectedLightType, setSelectedLightType] = useState(initialData?.light_type_name);
    const [selectedGuideline, setSelectedGuideline] = useState(null);
    const [definedConfiguration, setDefinedConfiguration] = useState(initialData?.configuration ?? null);

    const specifyGuideline = () => {
        if (!initialData) return
        const {configuration: {color, color_alter, color_alter_ms_delta}} = initialData
        if (!color) return
        if (!color_alter && !color_alter_ms_delta) return setSelectedGuideline(`SINGLE`)
        setSelectedGuideline(`DOUBLE`)
    }

    useEffect(
        () => {
            specifyGuideline()
        },
        []
    )

    return (
        <tr key={key}>
            <td>
                <div className="page-config select-container page-number">
                    <Select
                        placeholder="Select page"
                        options={[...Array(constants.pagesCount)].map((
                            _,
                            i
                        ) => (
                            {value: i + 1, label: i + 1}
                        ))}
                        value={{value: selectedPage, label: selectedPage}}
                        onChange={({value}) => setSelectedPage(value)}
                    />
                </div>
            </td>
            <td>
                <div className="page-config select-container light-type">
                    <Select placeholder="Select light type"
                            options={constants.availableLightTypes.map(({name}) => new Option(
                                name,
                                name
                            ))}
                            isDisabled={!selectedPage}
                            value={{value: selectedLightType, label: selectedLightType}}
                            onChange={({value}) => setSelectedLightType(value)}
                    />
                </div>
            </td>
            <td>
                <div className="page-config container config-specification">
                    <Select
                        placeholder="Choose guideline"
                        options={Object.entries(constants.availableGuidelines)
                            .map(([key, value]) => (
                                {
                                    label: value.description, value: key
                                }
                            ))}
                        value={{
                            value: selectedGuideline,
                            label: constants.availableGuidelines[selectedGuideline]?.description ?? ""
                        }}
                        onChange={({value}) => setSelectedGuideline(value)}
                        isDisabled={!selectedPage || !selectedLightType}
                    />
                    {!selectedGuideline
                        ? null
                        : (
                            () => {
                                switch (selectedGuideline) {
                                    case `SINGLE`:
                                        return <PageConfigSingleColorGuideline
                                            initialConfig={definedConfiguration ?? {}}
                                            onDataChange={data => setDefinedConfiguration(data)}
                                        />
                                    case `DOUBLE`:
                                        return <PageConfigDoubleColorGuideline
                                            initialConfig={definedConfiguration ?? {}}
                                            onDataChange={data => setDefinedConfiguration(data)}
                                        />
                                    default:
                                        return <p>Unknown guideline</p>
                                }
                            }
                        )()}
                </div>
            </td>
            <td>
                <div className="page-config container actions">
                    {!definedConfiguration
                        ? null
                        : <button
                            onClick={() => onDataSubmit({
                                page_number: selectedPage, light_type_name: selectedLightType,
                                configuration: definedConfiguration
                            })}
                            className={`${initialData
                                ? "update-button"
                                : "create-button"}`}>
                            {initialData
                                ? "Update"
                                : "Create"}
                        </button>}
                    {initialData
                        ? <button onClick={onDelete}
                                  className="delete-button">Delete</button>
                        : null}
                    <button onClick={() => {
                        setSelectedPage(initialData?.page)
                        setSelectedLightType(initialData?.light_type_name)
                        specifyGuideline()
                        setDefinedConfiguration(initialData?.configuration ?? null)
                    }}>Reset
                    </button>
                </div>
            </td>
        </tr>
    )
}

/**
 * @callback onSingleColorChange
 * @param {{color: int} | null} data
 */

/**
 *
 * @param {{color: int}} initialConfig
 * @param {onSingleColorChange} onDataChange
 * @returns {Element}
 * @constructor
 */
function PageConfigSingleColorGuideline({initialConfig, onDataChange}) {
    const [mutableConfig, setMutableConfig] = useState({...initialConfig});
    useEffect(
        () => {
            if (!mutableConfig.color) onDataChange(null); else onDataChange({color: mutableConfig.color});
        },
        [mutableConfig]
    )
    return (
        <div className="config-spec-guideline container single-color-guideline">
            <label>{`Color: `}
                <input
                    value={`#${(
                        mutableConfig.color ?? 0
                    ).toString(16)
                        .padStart(
                            6,
                            "0"
                        )}`}
                    onChange={({target: {value}}) => {
                        setMutableConfig({
                            ...mutableConfig, color: parseInt(
                                value.slice(1),
                                16
                            )
                        })

                    }}
                    type="color"
                />
            </label>
        </div>
    )
}

/**
 * @callback onDoubleColorChange
 * @param {{color: int, color_alter: int, color_alter_ms_delta: int} | null} data
 */

/**
 *
 * @param {{color: int, color_alter: int, color_alter_ms_delta: int}} initialConfig
 * @param {onDoubleColorChange} onDataChange
 * @returns {Element}
 * @constructor
 */
function PageConfigDoubleColorGuideline({initialConfig, onDataChange}) {
    const [mutableConfig, setMutableConfig] = useState({...initialConfig});
    useEffect(
        () => {
            if (!mutableConfig.color || !mutableConfig.color_alter
                || !mutableConfig.color_alter_ms_delta) onDataChange(null); else onDataChange({
                color: mutableConfig.color, color_alter: mutableConfig.color_alter,
                color_alter_ms_delta: mutableConfig.color_alter_ms_delta
            });
        },
        [mutableConfig]
    )
    return (
        <div className="config-spec-guideline container two-color-guideline">
            <label>Color 1:
                <input
                    value={`#${(
                        mutableConfig.color ?? 0
                    ).toString(16)
                        .padStart(
                            6,
                            "0"
                        )}`}
                    type="color"
                    onChange={({target: {value}}) => {
                        setMutableConfig({
                            ...(
                                mutableConfig ?? {}
                            ), color: parseInt(
                                value.slice(1),
                                16
                            )
                        })
                    }}
                />
            </label>
            <label>Color 2:
                <input
                    value={`#${(
                        mutableConfig.color_alter ?? 0
                    ).toString(16)
                        .padStart(
                            6,
                            "0"
                        )}`}
                    type="color"
                    onChange={({target: {value}}) => setMutableConfig({
                        ...(
                            mutableConfig ?? {}
                        ), color_alter: parseInt(
                            value.slice(1),
                            16
                        )
                    })}
                />
            </label>
            <label>Time delta (ms):
                <input
                    value={mutableConfig.color_alter_ms_delta ?? 1000}
                    type="number"
                    min="100"
                    onChange={({target: {value}}) => setMutableConfig({
                        ...(
                            mutableConfig ?? {}
                        ), color_alter_ms_delta: parseInt(value)
                    })}
                />
            </label>
        </div>
    )
}

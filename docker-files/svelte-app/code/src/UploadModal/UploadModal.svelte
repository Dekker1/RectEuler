<script>
    import {closeModal} from 'svelte-modals'
    import * as d3 from 'd3'
    import Table from "./Table.svelte";
    import ImagePreview from "./ImagePreview.svelte";
    import {createEventDispatcher} from 'svelte';
    import {Button, Popover} from 'sveltestrap';

    // provided by <Modals />
    export let isOpen
    let dialog; // HTMLDialogElement
    $: if (dialog && isOpen) dialog.showModal();

    export let title
    export let message

    let UploadPromise;


    let files;
    let images;
    let JSONConfig = null;
    $: delimiter = ",";
    $:fileContent = undefined
    let CSVData;
    let parseSuccessful = false;
    let JSONUploadInput;
    let JSONData;
    let emailAdress = ""

    let imagesArray = []
    $:imagesArray
    let imagesInput

    $:imageErrors = []
    $:JSONErrors = []
    $:CSVParseErrors = []
    $:JSONFields = []
    $:SucessMessages = []

    let JSONSelectedValue
    let dispatch = createEventDispatcher()

    sayHello()
    $:{
        fileContent
        delimiter
        if (fileContent) {
            try {
                CSVData = parse(fileContent)
            } catch (err) {
                CSVParseErrors.push(err.name);
                CSVData = undefined

            }
        }
    }

    function parse(f) {

        let matrix = []
        let header = []
        let firstCol = []

        const dsv = d3.dsvFormat(delimiter);
        matrix = dsv.parseRows(f)

        header = matrix.shift()
        header.shift()

        if (header.length === 0) {
            throw new Error("CSV Error: Empty Header!")
        }


        let rowLength = header.length

        for (const row of matrix) {
            if (row.length - 1 !== rowLength) {
                throw new Error("CSV Error: Not all rows have same length!")
            }
            firstCol.push(row.shift())
        }

        matrix = matrix.map(function (row) {
            return row.map(function (cell) {
                if ((cell === 'true') || (cell === '1') || (cell === 1)) {
                    return true

                }
                if ((cell === 'false') || (cell === '0') || (cell === 0)) {
                    return false
                }
                throw new Error(`CSV Error: Could not parse "${cell}"!`)


            });
        })

        return {matrix: matrix, header: header, firstCol: firstCol}
    }

    async function doPost() {

        const formData = new FormData()
        for (const image of imagesArray) {
            formData.append('images', image)
        }
        formData.append("CSV", JSON.stringify(CSVData))
        formData.append("delimiter", delimiter)
        formData.append("configJSON", JSON.stringify(JSONConfig))
        formData.append("JSONKey", JSONSelectedValue)
        formData.append("email", emailAdress)

        const res = await fetch('./api/uploaddata', {
            method: 'POST',
            body: formData
        })

        if (res.status === 200) {
            let result = await res.json();
            window.history.pushState({"token": result.token}, "", result.id);
            //location.reload();
            return result

        } else {
            const error = new Error(res.statusText)
            error.status = res.status
            error.json = await res.json()
            throw error
        }

    }

    function upload(){

        UploadPromise = doPost();

         UploadPromise.then(() => {
             console.log("upload success")
             sayHello()
         })


    }

    function sayHello() {
        console.log("send event")
        dispatch('uploadsuccess', {
            text: 'Hello!'
        });
    }

    const onFileSelected = (e) => {
        let file = e.target.files[0];
        let reader = new FileReader();
        reader.readAsText(file);
        reader.onload = e => {
            fileContent = null

            fileContent = e.target.result
        };
    }


    const onJSONFileSelected = (e) => {
        if (e.target.files.length === 0) {
            JSONConfig = null
            JSONErrors = []
            return
        }
        let file = e.target.files[0];
        let reader = new FileReader();
        reader.readAsText(file);
        reader.onload = e => {
            let content = JSON.parse(e.target.result)
            validateConfigFile(content)
        };
    }


    function validateConfigFile(configFile) {
        JSONErrors = []
        JSONConfig = null
        if (!"data" in configFile) {
            JSONErrors.push("Filed 'data' missing!")
            return false
        }
        if (!"settings" in configFile) {
            JSONErrors.push("Filed 'settings' missing!")
            return false
        }
        let fields = new Set()
        for (const value of Object.values(configFile.data)) {

            for (const field of Object.keys(value)) {
                fields.add(field)
            }
        }

        for (const [key, value] of Object.entries(configFile.data)) {
            for (const field of fields) {
                if (!(field in value)) {
                    JSONErrors.push(`In ${key} field ${field} missing!`)
                } else {
                    if (!["name", "file"].includes(field) && !Number.isFinite(value[field])) {
                        JSONErrors.push(`In ${key} field ${field} is not numeric!`)

                    }
                }
            }
        }
        JSONConfig = configFile
        JSONErrors = JSONErrors
        JSONFields = [...fields].filter(field => !["name", "file"].includes(field))
        if (JSONFields.length > 0) {
            JSONSelectedValue = JSONFields[0]

        }
        if (JSONErrors.length === 0) {
            validateImages()

        }
    }


    // remove indexed value
    const handleRemove = (index) => {
        imagesArray = [
            ...imagesArray.slice(0, index),
            ...imagesArray.slice(index + 1, imagesArray.length)
        ];
        validateImages()
    };


    function addImages() {
        imagesArray = [...imagesArray, ...imagesInput.files]
        imagesArray.sort((a, b) => a.name.localeCompare(b.name))
        imagesInput.value = "";
        validateImages()
    }


    function validateImages() {
        imageErrors = []

        const imageNames = imagesArray.map(image => image.name);
        const lookup = imageNames.reduce((a, e) => {
            a[e] = ++a[e] || 0;
            return a;
        }, {});

        let duplicates = new Set(imageNames.filter(e => lookup[e]))

        for (const name of duplicates) {
            imageErrors.push(`File ${name} duplicated!`)

        }

        if (!JSONConfig || JSONErrors.length > 0) {
            imageErrors.push("JSON Configuration File missing or corrupt!")
            return
        }


        let fileSizeSum = Object.values(JSONConfig.data).reduce((acc, val) => acc + val.file.size, 0)

        if (fileSizeSum > 10000000) {
            imageErrors.push("Files to upload are too big! Maximum of 10 Mb exceeded")

        }


        for (const [key, value] of Object.entries(JSONConfig.data)) {
            if (!imageNames.includes(value.file)) {
                imageErrors.push(`File ${value.file} for key ${key} missing in uploads!`)

            }
        }
        imageErrors = imageErrors
    }

    $:hasErrors = imageErrors.length > 0 || JSONErrors.length > 0

</script>

    <dialog
            bind:this={dialog}
            on:close={() => (isOpen = false)}
            on:click|self={() => dialog.close()}
            on:uploadsuccess
    >
    <div role="dialog" class="modal">
        <div class="contents">
            <div class="form-group">
                <!--                <div class="form-row">-->
                <!--                    <div class="input-group mb-3">-->
                <div class="input-group mb-3">
                    <label for="CSVUpload" class="form-label">Upload CSV:</label>
                    <div class="input-group">
                        <input class="form-control" id="CSVUpload" type="file" accept=".csv" bind:files
                               on:change={(e)=>onFileSelected(e)}>
                        <Button outline secondary id={`btn-right-info-csv`}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                                 class="bi bi-info-circle" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                            </svg>
                        </Button>
                        <Popover placement="right" target="btn-right-info-csv">
                            <div slot="title">
                                <b>CSV</b>
                            </div>
                            The CSV contains the set names in the first row, where the value of the first, left most cell does not matter. The first column contains the element names. An binary matrix indicates which element is contained in which set. <a href="/static/harrypotter.csv">Example dataset!</a>
                        </Popover>
                        <!--                        <button type="button" class="btn btn-outline-secondary" data-toggle="popover"-->
                        <!--                            data-content="And here's some amazing content. It's very engaging. Right?"> U+F431</button>-->
                    </div>

                    <!--                    </div>-->
                </div>
                <div class="input-group mb-3">
                    <!--                    <div class="col-auto my-1">-->
                    <label for="CSVUploadDelimiter" class="input-group-text">Delimiter:</label>
                    <!--                    </div>-->
                    <!--                    <div class="col-auto my-1">-->
                    <input class="form-control" list="CSVUploadDelimiterOptions" id="CSVUploadDelimiter"
                           placeholder="Type to search..." bind:value={delimiter}>
                    <datalist id="CSVUploadDelimiterOptions">
                        <option value=";"></option>
                        <option value=","></option>
                        <option value=" ">Space</option>
                        <option value="\t">Tab</option>
                    </datalist>
                    <!--                    </div>-->
                    <Button outline secondary id={`btn-right-info-delimiter`}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                             class="bi bi-info-circle" viewBox="0 0 16 16">
                            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                            <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                        </svg>
                    </Button>
                    <Popover placement="right" target="btn-right-info-delimiter">
                        <div slot="title">
                            <b>Delimiter</b>
                        </div>
                        The delimiter to split the uploaded CSV.
                    </Popover>
                </div>
                <div class="input-group mb-3">

                    {#if CSVData}
                        <Table data={CSVData.matrix} head={CSVData.header} firstcol="{CSVData.firstCol}"/>
                    {:else}
                        <div class="mb-3 input-group">
                            No CSV Uploaded.
                        </div>
                    {/if}
                </div>
            </div>
            <h2 class="text-divider"><span>Coming Soon!</span></h2>
            <div class="form-group">
                <div class="input-group mb-3">
                    <label for="ImageUpload" class="form-label">Upload Images:</label>
                    <div class="input-group" >
                        <input
                                class="form-control"
                                id="ImageUpload"
                                multiple
                                type="file"
                                accept=".jpg, .png, .bmp, .jpeg, .svg"
                                bind:this={imagesInput}
                                on:change={addImages}
                                disabled
                        />
                        <Button outline secondary id={`btn-right-info-images`} disabled>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                                 class="bi bi-info-circle" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                            </svg>
                        </Button>
                        <Popover placement="right" target="btn-right-info-images">
                            <div slot="title">
                                <i>Hello</i> <b>World!</b>
                            </div>
                            This Popover has HTML in the title passed as a slot.
                        </Popover>
                    </div>
                </div>
            </div>
            <h2 class="text-divider"><span>Coming Soon!</span></h2>
            <div class="form-group">
                <!--                <div class="input-group">-->
                <label for="JSONUpload" class="form-label">Upload JSON with additional attributes:</label>
                <div class="input-group mb-3">
                    <input class="form-control" id="JSONUpload" type="file" accept=".json"
                           bind:this={JSONUploadInput}
                           bind:files={JSONData}
                           on:change={(e)=>onJSONFileSelected(e)}
                           disabled>
                    <Button outline secondary id={`btn-right-info-json`} disabled>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                             class="bi bi-info-circle" viewBox="0 0 16 16">
                            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                            <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                        </svg>
                    </Button>
                    <Popover placement="right" target="btn-right-info-json">
                        <div slot="title">
                            <i>JSON</i> <b>Upload</b>
                        </div>
                        You can add additional data attributes via a JSON file.
                        This file has to be of the following form:

                    </Popover>
                </div>
                <div class="input-group mb-3">
                    <label for="JSONKey" class="input-group-text">JSON Key for scaling:</label>
                    <select class="form-control" bind:value={JSONSelectedValue} id="JSONKey" disabled>
                        {#each JSONFields as field, i}
                            <option value={field}>
                                {field}
                            </option>
                        {/each}
                    </select>
                    <Button outline secondary id={`btn-right-info-scale`} disabled>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"
                             class="bi bi-info-circle" viewBox="0 0 16 16">
                            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                            <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                        </svg>
                    </Button>
                    <Popover placement="right" target="btn-right-info-scale">
                        <div slot="title">
                            <i>Hello</i> <b>World!</b>
                        </div>
                        This Popover has HTML in the title passed as a slot.
                    </Popover>
                </div>
                <!--                </div>-->
            </div>

            <div class="imagePreview">
                <div class="d-flex flex-wrap">

                    {#each imagesArray as image, index }
                        <ImagePreview inputFile={image} removeFn={()=>handleRemove(index)}></ImagePreview>
                    {/each}
                </div>
            </div>

<!--            <h2 class="text-divider"><span>Optional</span></h2>-->

<!--            <div class="form-group">-->
<!--                <div class="input-group mb-3">-->
<!--                    <label for="JSONUpload" class="form-label">Notification on completion:</label>-->
<!--                    <div class="input-group">-->
<!--                        <label for="JSONKey" class="input-group-text">Email:</label>-->
<!--                        <input type="email" class="form-control" bind:value={emailAdress}/>-->
<!--                        <Button outline secondary id={`btn-right-info-email`}>-->
<!--                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor"-->
<!--                                 class="bi bi-info-circle" viewBox="0 0 16 16">-->
<!--                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>-->
<!--                                <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>-->
<!--                            </svg>-->
<!--                        </Button>-->
<!--                        <Popover placement="right" target="btn-right-info-email">-->
<!--                            <div slot="title">-->
<!--                                <i>Hello</i> <b>World!</b>-->
<!--                            </div>-->
<!--                            This Popover has HTML in the title passed as a slot.-->
<!--                        </Popover>-->
<!--                    </div>-->
<!--                </div>-->
<!--            </div>-->
            <h2 class="text-divider"></h2>
            <div class="form-group">
                <div class="input-group mb-3">
                    <button class="form-control" on:click={upload} disabled='{false && !parseSuccessful}'>Upload
                    </button>
                </div>
                <div class="InfoContainer">
                    {#if UploadPromise}
                        {#await UploadPromise}
                        {:then message}
                            <div class="alert alert-success alert-dismissible" role="alert">
                                {message}
                            </div>
                        {:catch error}
                            <div class="alert alert-danger alert-dismissible" role="alert">
                                {error}
                            </div>
                        {/await}
                    {/if}

                    {#each SucessMessages as message}
                        <div class="alert alert-success alert-dismissible" role="alert">
                            {message}
                        </div>
                    {/each}
                    {#each [...JSONErrors, ...imageErrors] as error}
                        <div class="alert alert-danger alert-dismissible" role="alert">
                            {error}
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>


</dialog>

<style>

    div .form-row {
        display: flex;
    }

    .modal {
        position: fixed;
        top: 0;
        bottom: 0;
        right: 0;
        left: 0;
        display: flex;
        justify-content: center;
        align-items: center;

        /* allow click-through to backdrop */
        pointer-events: none;

    }

    .contents {
        min-width: 240px;
        border-radius: 6px;
        padding: 16px;
        background: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        pointer-events: auto;
        max-width: 50%;
    }

    h2 {
        text-align: center;
        font-size: 24px;
    }

    p {
        text-align: center;
        margin-top: 16px;
    }

    .actions {
        margin-top: 32px;
        display: flex;
        justify-content: flex-end;
    }

    .imagePreview {
        max-height: 500px;
        overflow-y: scroll;
    }


    #fileToUpload {
        color: transparent;
        overflow: hidden;
    }

    .InfoContainer {
        max-height: 250px;
        overflow-y: auto;
    }

    .flex-box {
        display: flex;
        border: lightgray 1px solid;
        padding: 2px;
    }

    .center {
        border: 1px solid;
        display: flex;
        justify-content: center;
        background: lightgray;
        min-height: 50px;
        align-items: center;
    }


    .text-divider {
        margin: 2em 0;
        line-height: 0;
        text-align: center;
        color: lightgray;
        font-size: 12px
    }

    .text-divider span {
        background-color: #ffffff;
        padding: 1em;
    }

    /*.text-divider h2{color: lightgray;}*/
    .text-divider:before {
        content: " ";
        display: block;
        border-top: 1px solid #e3e3e3;
        border-bottom: 1px solid #f7f7f7;
    }

</style>

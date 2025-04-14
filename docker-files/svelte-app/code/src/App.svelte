<svelte:head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css">
</svelte:head>

<script>
    import {
        Row,
        Col,
        Navbar,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
        Button,
        Collapse,
        Nav,
        Dropdown,
        NavbarToggler
    } from 'sveltestrap';
    import TabPane from "./Tabs/TabPane.svelte";
    import TabContent from "./Tabs/TabContent.svelte";

    import OverallStatistics from "./OverallStatistics/OverallStatistics.svelte";
    import url from "./url.js";
    import EulerDiagramGroup from "./EulerDiagramGroup/EulerDiagramGroup.svelte";
    import {onMount, onDestroy} from "svelte";

    import {activeTab, ID} from "./store.js"
    import IndividuslStatistics from "./IndividuslStatistics/IndividuslStatistics.svelte";
    import UploadModal from "./UploadModal/UploadModal.svelte";
    import {Modals, closeModal, openModal} from 'svelte-modals'
    import SliderBarGraph2 from "./SliderBarGraph2/SliderBarGraph2.svelte";
    import {Circle2} from 'svelte-loading-spinners';

    import {jsPDF} from 'jspdf'
    import 'svg2pdf.js'
    import {
        Canvg,
        presets
    } from 'canvg'
    import ViewSettings from "./ViewSettings/ViewSettings.svelte";

    let data = null
    let currentDiagram;
    let exampleDatasetNames

    $:token = getEditToken();
    $:$ID = getID();

    let poller
    let apiData

    let layoutOptimizationStep = {}

    let splittingStrategy = getStrategyFromURL()
    let status


    const setupPoller = (id) => {
        if (poller) {
            clearInterval(poller)
        }
        poller = setInterval(doPoll(id), 5000)
    }

    const doPoll = (id) => async () => {
        location.reload();
        /*
        console.log(`polling ${id}`)
        await new Promise(resolve => setTimeout(async () => {
            const res = await fetch(`./api/getdata/${id}`);
            const jsonres = await res.json()
            const res_status = await fetch(`./api/getstatus/${$ID}`);
            const jsonres_status = await res_status.json()
            status = jsonres_status
            apiData = jsonres
        }, 5000))

         */
    }


    function getID() {
        if ($url.pathname.split("/").length > 0) {
            return $url.pathname.split("/")[1]
        }
        return null
    }


    function getStrategyFromURL() {
        console.log($url.searchParams)
        if ($url.searchParams.get('strategy')) {
            console.log($url.searchParams.get('strategy'))
            return $url.searchParams.get('strategy')

        }
        return null
    }

    function getEditToken() {
        return $url.searchParams.get('token');
    }

    let splitSortDict = {
        "noSplit": 0,
        "recursiveclusterSplit": 1,
        "randomSplit": 2
    };

    let splittingStrategys = []

    function getStrategies(dict) {
        let items = Object.keys(apiData).map(function (key) {
            return [key, splitSortDict[key]];
        });
        console.log(items)

        items.sort(function (first, second) {
            return first[1] - second[1];
        });

        items = items.map(function (item) {
            return item[0];
        });
        return items;
    }


    onMount(async () => {

        const exampleDatasetNamesJSON = await fetch(`./api/examples/`)
        exampleDatasetNames = await exampleDatasetNamesJSON.json()

        if (!$ID) {
            for (const dataset of exampleDatasetNames) {
                if (dataset.dataset_name === "animals") {
                    $ID = dataset.job_id
                    window.history.pushState('','',dataset.job_id);

                }
            }
        }
        const res_status = await fetch(`./api/getstatus/${$ID}`);
        const jsonres_status = await res_status.json()
        status = jsonres_status
        if ((status === "RUNNING" || status === "QUEUED")) {
            setupPoller($ID)
        }
        const res = await fetch(`./api/getdata/${$ID}`);
        const jsonres = await res.json()

        console.log(status)
        apiData = jsonres
        if (apiData) {

            splittingStrategys = getStrategies(apiData)
            console.log(splittingStrategys)
            if (!splittingStrategy) {
                splittingStrategy = splittingStrategys[0]

            }
            currentDiagram = apiData[splittingStrategy];
            console.log(currentDiagram)

            layoutOptimizationStep = {}

            for (const [key, sublayout] of Object.entries(currentDiagram)) {
                layoutOptimizationStep[key] = sublayout.length - 1
            }
        }


    });


    // openModal(UploadModal)


    function handleClickPDF() {
        let SVG = document.getElementById('EulerSVG')
        let outerGbBox = document.getElementById('outerG').getBoundingClientRect();
        let SVGbBox = SVG.getBoundingClientRect()
        let doc = new jsPDF({
            orientation: "landscape",
            unit: "px",
            format: [outerGbBox.width + 20, outerGbBox.height + 20]

        })


        doc.svg(SVG, {
            x: -outerGbBox.x + 10 + SVGbBox.x,
            y: -outerGbBox.y + 10 + SVGbBox.y,
            width: SVGbBox.width,
            height: SVGbBox.height,
            loadExternalStyleSheets: true
        })
            .then(() => {
                // save the created pdf
                doc.save('rectEuler.pdf')
            })


    }

    async function toPng(data) {
        const preset = presets.offscreen()

        const {
            width,
            height,
            svg
        } = data

        const canvas = new OffscreenCanvas(width, height)
        const ctx = canvas.getContext('2d')

        const v = await Canvg.fromString(ctx, svg, preset)
        // Render only first frame, ignoring animations and mouse.
        v.resize(width, height, 'xMidYMid meet')

        await v.render()

        const blob = await canvas.convertToBlob()
        const pngUrl = URL.createObjectURL(blob)

        return pngUrl
    }

    function handleClickPNG() {
        let SVG = document.getElementById('EulerSVG')
        let outerGbBox = document.getElementById('outerG').getBoundingClientRect();

        let s = new XMLSerializer();
        let str = s.serializeToString(SVG);
        toPng({
            width: outerGbBox.width,
            height: outerGbBox.height,
            svg: str
        }).then((pngUrl) => {

            let download = document.createElement('a');
            download.href = pngUrl
            download.download = `${$ID}.png`;
            download.click();
        })
    }


    function uploadSuccess(event) {
        console.log(event)
        console.log("get upload event")
        location.reload();
        /*
        alert(event.detail.text);
        const res_status = await fetch(`./api/getstatus/${$ID}`);
        const jsonres_status = await res_status.json()
        status = jsonres_status
        if ((status === "RUNNING" || status === "QUEUED")) {
            setupPoller($ID)
        }
*/
    }

    function tabChange(e) {
        $activeTab = e.detail
    }

    let showModal = false;


    const onChange = () => {
        currentDiagram = apiData[splittingStrategy];
        layoutOptimizationStep = {}

        for (const [key, sublayout] of Object.entries(currentDiagram)) {
            layoutOptimizationStep[key] = sublayout.length - 1
        }
    }
    let currentEulerDiagramSublayouts = {}
    $:{
        if (currentDiagram) {
            currentEulerDiagramSublayouts = {}

            for (const [sublayoutID, optimizationstep] of Object.entries(layoutOptimizationStep)) {
                currentEulerDiagramSublayouts[sublayoutID] = currentDiagram[sublayoutID][optimizationstep]
            }


        }

    }

    let isOpen = false;

    function handleUpdate(event) {
        isOpen = event.detail.isOpen;
    }

    let isOpenSettings = false;

    function toggleVisibleSettings() {
        isOpenSettings = !isOpenSettings
    }


</script>
<div class="h-100 d-flex flex-column">

    <Navbar color="light" light expand="md">
        <div>
            <a class="navbar-brand" href="#">RectEuler</a>
            by
        </div>
        <div>
            <a class="navbar-brand" href="https://www.cgmi.uni-konstanz.de/" style="margin-left: 5px">
                <img src="/static/logo_uni_kn.svg" height="40px" class="d-inline-block align-top"
                     alt="">
                Visual Computing
            </a>
        </div>
        <div>
            supported by
            <a class="navbar-brand" href="http://www.gurobi.com" style="margin-left: 5px">Gurobi</a>
        </div>
        <div>
            <a class="navbar-brand" href="https://github.com/PatrickPaetzold/RectEuler" style="margin-left: 25px">Get Code!</a>
        </div>
        
        <!--        </div>-->
        <NavbarToggler on:click={() => (isOpen = !isOpen)}/>
        <Collapse {isOpen} navbar expand="md" on:update={handleUpdate}>
            <Nav class="ms-auto" navbar>
                {#if exampleDatasetNames}
                    <Dropdown nav inNavbar>
                        <DropdownToggle class="mx-2 my-2" caret>Existing Datasets</DropdownToggle>
                        <DropdownMenu end>
                            {#each exampleDatasetNames as d}

                                <DropdownItem href="{d.job_id}">{d.dataset_name}</DropdownItem>

                            {/each}

                        </DropdownMenu>
                    </Dropdown>
                {/if}
                <!--        <NavItem>-->
                <Button class="mx-2 my-2" nav on:click={() => (showModal = true)}>Upload Data</Button>
                <!--        </NavItem>-->
                {#if apiData}
                    <Button class="mx-2 my-2" on:click={handleClickPDF}>To PDF</Button>

                    {#if splittingStrategys.length > 1 }
                        <Dropdown nav inNavbar>
                            <DropdownToggle class="mx-2 my-2" caret>{splittingStrategy}</DropdownToggle>
                            <DropdownMenu end>
                                {#each splittingStrategys as splittingStrategy}

                                    <DropdownItem
                                            href="{$ID}?strategy={splittingStrategy}">{splittingStrategy}</DropdownItem>

                                {/each}

                            </DropdownMenu>
                        </Dropdown>
                    {:else }
                        {splittingStrategy}
                    {/if}
                {/if}
            </Nav>
        </Collapse>
    </Navbar>

    {#if currentDiagram}
        <div class="content">
            <EulerDiagramGroup data={currentEulerDiagramSublayouts}/>
        </div>
        <div class="ButtonSettings {isOpenSettings === true ? 'container-setting-close' : 'container-settings'}">
            <div class="button iconbutton">
                <Button color="primary" on:click={toggleVisibleSettings}>
                    Settings
                </Button>
            </div>
        </div>
        {#if isOpenSettings}
            <footer class="footer" >
                <div class="container-fluid">
                    <Row>
                        <Col xs="10">
                            <TabContent on:tab={tabChange}>
                                {#if Object.keys(currentDiagram).length > 1}
                                    {#each Object.entries(currentDiagram) as [sublayoutID, sublayoutData]}
                                        <TabPane tabId="{sublayoutID}" tab="Layout {sublayoutID}" active>
                                            <Row>
                                                <Col xs="6">
                                                    <SliderBarGraph2 {sublayoutID} data={sublayoutData}
                                                                     bind:layoutOptimizationStep={layoutOptimizationStep[sublayoutID]}/>
                                                </Col>
                                                <Col xs="6">
                                                    <IndividuslStatistics
                                                            data={sublayoutData[layoutOptimizationStep[sublayoutID]]}
                                                            layoutID={sublayoutID}/>

                                                </Col>
                                            </Row>
                                        </TabPane>

                                    {/each}
                                {/if}
                                <TabPane tab="Overall Statistics" tabId="Overall" active>
                                    <Row>
                                        {#if Object.keys(currentDiagram).length === 1}
                                            <Col xs="4">
                                                <SliderBarGraph2 sublayoutID=0
                                                                 data={currentDiagram[0]}
                                                                 bind:layoutOptimizationStep={layoutOptimizationStep[0]}/>
                                            </Col>
                                            <Col xs="8">
                                                <OverallStatistics data={currentEulerDiagramSublayouts}
                                                                   {layoutOptimizationStep}/>
                                            </Col>
                                        {:else}
                                            <Col>
                                                <OverallStatistics data={currentEulerDiagramSublayouts}
                                                                   {layoutOptimizationStep}/>
                                            </Col>
                                        {/if}
                                    </Row>
                                </TabPane>
                            </TabContent>
                        </Col>
                        <Col xs="2">
                            <ViewSettings/>
                        </Col>
                    </Row>
                </div>
            </footer>
        {/if}


    {/if}

    {#if (status === "QUEUED" || status === "RUNNING")}
        <div class="backdrop">
            <div class="spinner">
                <Circle2 colorOuter="#1F77B4" colorCenter=" #FF7F0E" colorInner="#e2e2e2"></Circle2>
                <p style="margin: 5px; font-weight: lighter; font-size: larger">Waiting for optimization to finish</p>

            </div>

        </div>
    {/if}

    {#if status === "TIMEOUT" || status === "ERROR"}
        <div class="backdrop">
            <div class="spinner">
                <p style="margin: 5px; font-weight: lighter; font-size: larger">No Solution found!</p>

            </div>

        </div>
    {/if}
</div>


<UploadModal bind:isOpen="{showModal}" on:uploadsuccess={uploadSuccess}/>

<style>
    footer {
        background-color: white;
        float: left;
        position: absolute;
        width: 100%;
        height: 230px;
        bottom: 0;

    }

    .backdrop {
        position: fixed;
        top: 0;
        bottom: 0;
        right: 0;
        left: 0;
        background: rgba(0, 0, 0, 0.50);
        z-index: 999
    }

    .spinner {
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
        margin: 5px;
    }

    .content {
        height: calc(100% - 60px);
        padding: 5px;
    }

    .container-settings {
        position: fixed;
        bottom: 50px;
        right: 50px;
        cursor: pointer;
    }

    .container-setting-close {
        position: fixed;
        bottom: 270px;
        right: 50px;
        cursor: pointer;
    }

    @media (max-width: 480px) {
        .ButtonSettings {
            display: none;
        }
    }
</style>


<script>

    import EulerDiagram from "../EulerDiagram/EulerDiagram.svelte";
    import * as d3 from 'd3'
    import ColorPicker from "../ColorPicker/ColorPicker.svelte";
    import ConnectingLines from "../ConnectingLines/ConnectingLines.svelte";


    export let data;

    let count = 0

    let tableaucolors
    $:tableaucolors = ["#1F77B4", "#AEC7E8", "#FF7F0E", "#FFBB78", "#2CA02C", "#98DF8A", "#D62728", "#FF9896", "#9467BD", "#C5B0D5", "#8C564B", "#C49C94", "#E377C2", "#F7B6D2", "#7F7F7F", "#C7C7C7", "#BCBD22", "#DBDB8D", "#17BECF", "#9EDAE5"]
    let el
    let innit_scale = null
    let h;
    let bindHandleZoom, bindInitZoom;
    let x_transform = 0
    let y_transform = 0

    let widths = []
    let heights = []
    let offsets = []
    let ports = []
    $:{

        count++
    }

    $:{
        widths = Array(Object.values(data).length).fill(-1)
        heights = Array(Object.values(data).length).fill(-1)
        offsets = Array(Object.values(data).length).fill(-1)
        ports = Array(Object.values(data).length).fill(-1)

    }

    $:{

        let setIDtoSetName

        setIDtoSetName = {}
        for (const diagram of Object.values(data)) {
            for (const rect of diagram.rects) {
                setIDtoSetName[rect.ID] = rect.name.text
            }
        }

        if (Object.keys(setIDtoSetName).length > tableaucolors.length) {
            let difference = Object.keys(setIDtoSetName).length - tableaucolors.length
            for (let i = 0; i < difference; i++) {
                tableaucolors.push('#' + Math.floor(Math.random() * 16777215).toString(16))

            }
        }
    }


    $: if (bindInitZoom) {
        d3.select(bindInitZoom).call(zoomX);
    }
    $: zoomX = d3.zoom().on("zoom", handleZoom);

    function handleZoom(e) {
        //d3.select(bindHandleZoom).attr('transform', e.transform);
        scale = e.transform.k * innit_scale
        x_transform = e.transform.x
        y_transform = e.transform.y

    }


    let cp = {position: {x: 0, y: 0}, colorIDX: 0, visible: false, currentColor: "#ffffff"}

    function setNameClick(event) {
        cp.position = event.detail.position
        cp.colorIDX = retnum(event.detail.colorID)
        cp.visible = true
        cp.currentColor = event.detail.currentColor
    }

    function calculatedWidths(event) {
        let ID = event.detail.ID
        widths[ID] = event.detail.width
        heights[ID] = event.detail.height
        ports[ID] = event.detail.ports
        console.log(event)

    }

    function retnum(str) {
        let num = str.replace(/[^0-9]/g, '');
        return parseInt(num, 10);
    }


    let w;
    $:{
        w = 30 * (widths.length - 1)
        for (let my_w of widths) {
            w += my_w
        }

    }

    $:{
        if (Math.min(...widths) > -1) {
            let sum = 0
            for (let i = 0; i < widths.length; i++) {
                offsets[i] = sum
                sum += widths[i] + 30
            }

        }
    }

    let scale = 1

    $:{
        if (el && count === 1 && x_transform === 0 && Math.min(...heights) > -1) {

            let scalex = el.getBBox().x * 2 / w
            let scaley = (el.getBBox().y * 2 - 240) / Math.max(...heights)
            innit_scale = Math.min(scalex, scaley)
            scale = innit_scale
            x_transform = el.getBBox().x - (w * scale) / 2

        }
    }

    $:{
        //data;
        //ports = ports;
    }


</script>
<ColorPicker position={cp.position} colorIDX={cp.colorIDX} currentColor="{cp.currentColor}" bind:visible={cp.visible}
             bind:colors={tableaucolors}/>
<svg width="100%" height="100%" bind:this={bindInitZoom} id="EulerSVG"
>
    <circle cx="50%" cy="50%" r="1" style="visibility: hidden;" bind:this={el}/>

    <g class="outerG" id="outerG" bind:this={bindHandleZoom}
       transform="translate({x_transform},{y_transform}) scale({scale})">
        {#each Object.entries(data) as [layoutID, diagram]}
            <EulerDiagram {layoutID} {diagram} colors={tableaucolors}
                          on:setNameClick={setNameClick} offset={offsets[layoutID]} on:sizeCalculated={calculatedWidths}
            />
        {/each}


        <g class="ConnectingLines">
            <ConnectingLines offsets="{offsets}" ports="{ports}" colors="{tableaucolors}"/>
        </g>
    </g>

</svg>
<style>

</style>
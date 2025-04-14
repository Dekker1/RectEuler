<script>
    import {tweened} from "svelte/motion";
    import {createEventDispatcher} from 'svelte';
    import {tooltip} from '../Tooltip/tooltip.js';
    import EncodingCircle from "./EncodingCircle.svelte";
    import {activeIDsElementGroups, activeIDsSetNames, ID, activeLayoutElementGroup, HoveringActive} from "../store.js";

    export let id;
    export let position;
    export let size;
    export let elements;
    export let containedin;
    export let colors;
    export let setIDtoSetName;
    export let layoutID;

    const circleCols = 2
    const circleDiam = 10
    const circleMargin = {"left": 3, "right": 3, "top": 3, "bottom": 3}

    const transform_x_tween = tweened(position.x, {duration: 900})
    const transform_y_tween = tweened(position.y, {duration: 900})
    const width_tween = tweened(size.width, {duration: 900})
    const height_tween = tweened(size.height, {duration: 900})
    $: transform_x_tween.set(position.x)
    $: transform_y_tween.set(position.y)
    $: width_tween.set(size.width)
    $: height_tween.set(size.height)

    let currenthover = false;

    function retnum(str) {
        let num = str.replace(/[^0-9]/g, '');
        return parseInt(num, 10);
    }

    let circleExtent
    $: {
        containedin
        circleExtent = getCircleExtent();
    }

    function getCircleExtent() {
        let x = Math.min(circleCols, containedin.length) * (circleDiam + circleMargin.right + circleMargin.left)
        let y = Math.max(Math.ceil(containedin.length / circleCols), 1) * (circleMargin.top + circleMargin.bottom + circleDiam)
        return {"x": x, "y": y}
    }

    function getEncodingCirecles(containment) {
        let returnlist = []
        for (const [i, element] of containment.entries()) {
            let col = i % circleCols
            let row = Math.trunc(i / circleCols)
            let xPos = col * (circleDiam + circleMargin.left + circleMargin.right) + circleDiam / 2 + circleMargin.left
            let yPos = row * (circleDiam + circleMargin.top + circleMargin.bottom) + circleDiam / 2 + circleMargin.top

            returnlist.push({"x": xPos, "y": yPos, "ID": element.ID})
        }
        return returnlist
    }


    function handleMouseOver(event) {
        if ($HoveringActive) {
            containedin.forEach(item => $activeIDsElementGroups.add(item.ID))
            currenthover = true
            $activeIDsElementGroups = $activeIDsElementGroups
            $activeLayoutElementGroup = layoutID
        }


    }

    function handleMouseOut(event) {
        containedin.forEach(item => $activeIDsElementGroups.delete(item.ID))
        currenthover = false
        $activeIDsElementGroups = $activeIDsElementGroups
        $activeLayoutElementGroup = null

    }

    function isActiveIDs() {
        let isActive = false
        containedin.forEach(item => isActive |= $activeIDsSetNames.has(item.ID))
        return isActive
    }

    $: active = (!$activeIDsSetNames.size && !$activeIDsElementGroups.size) || $activeIDsElementGroups.has(id) || isActiveIDs() || currenthover;

    $: active_class = active ? "" : "inactive";
    let encodingCircles
    $:{
        encodingCircles = getEncodingCirecles(containedin)
    }
</script>

<g id={id} class="{active_class}" transform={`translate(${$transform_x_tween}, ${$transform_y_tween})`}
   on:mouseenter={handleMouseOver} on:mouseleave={handleMouseOut} pointer-events="all">
    <rect fill="white" height={circleExtent.y} rx="5" width={circleExtent.x}
          x={size.width - circleExtent.x} y="0"></rect>

    <rect class="element-rect" x="0" y="0" width={$width_tween}
          height={$height_tween}
          rx="5px" fill="none" stroke-width="2" stroke="black">
    </rect>

    {#each elements as element}
        {#if element.type === "Text"}
            <text class="element noHover" fill="black" pointer-events="none">
                <tspan font-family="Arial, Helvetica, sans-serif" font-size="16px" style="margin-left: 5px"
                       x={element.x+4}
                       y={element.y}>{element.text}</tspan>
            </text>
        {/if}
        {#if element.type === "Image"}
            <image class="element" title={element.text} height="{element.height}" width="{element.width}"
                   x={element.x} y={element.y} href="/api/image/{$ID}/{element.filename}" use:tooltip></image>
        {/if}
    {/each}


    <g transform={`translate(${size.width - getCircleExtent().x}, 0)`}>
        {#each encodingCircles as c}
            <EncodingCircle x={c.x} y={c.y} id={c.ID} diam={circleDiam} name={setIDtoSetName[c.ID]}
                            color="{colors[retnum(c.ID)]}"/>
        {/each}
    </g>

</g>
<style>
    .element-rect {
        fill-opacity: 0;
    }

    .inactive {
        stroke: lightgrey;
        opacity: 0.1;
        transition: all 0.5s ease;
        fill-opacity: 0;
        fill: lightgray;
    }

    .noHover {
        pointer-events: none;
    }
</style>
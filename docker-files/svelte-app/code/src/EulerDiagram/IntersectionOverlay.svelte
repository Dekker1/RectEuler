<script>
    import {hoveredDepth, hoveredLayoutIDs, hoveredStatus, enableOverlay} from "../store.js";

    export let points;
    export let depth;
    export let status;
    export let sets;
    export let layoutID;

    $:pointsCopy = points.slice(0)
    $:pointsCopy.splice(-1)
    $: d = "M" + pointsCopy.map(u => u[0] + "," + u[1]).join(' L ') + "Z"
    $:active = (status === $hoveredStatus && depth === $hoveredDepth && $hoveredLayoutIDs.has(layoutID + "")) ||$enableOverlay;
</script>

{#if active}
    <path d="{d}" opacity="0.2" class="{status} "></path>

{/if}
<style>
    .WantedFilledIntersection {
        fill: green;
    }

    .EmptyUnwantedIntersection {
        fill: red;
    }

    .EmptyWantedIntersection {
        fill: yellow;
    }

    .inactive {
        stroke: lightgrey;
        opacity: 0.1;
        transition: all 0.5s ease;
        fill-opacity: 0;
        fill: lightgray;
    }
</style>
<script>

    import {activeIDsElementGroups, activeIDsSetNames, activeLayoutElementGroup, outlineSaturation} from "../store.js";
    import {createEventDispatcher} from "svelte";
    import {tweened} from "svelte/motion";


    export let position
    export let size
    export let text
    export let id
    export let color
    export let layoutID
    let inactive = false;


    function handleMouseOver(event) {
        $activeIDsSetNames.add(id)
        $activeIDsSetNames = $activeIDsSetNames


    }

    function handleMouseOut(event) {
        $activeIDsSetNames.delete(id)
        $activeIDsSetNames = $activeIDsSetNames

    }


    const dispatch = createEventDispatcher();

    function handleMouseClick(event) {
        dispatch('setNameClick', {
            position: {x: event.x, y: event.y},
            colorID: id,
            currentColor: color
        });
    }

    $: active = ($activeIDsElementGroups.has(id) && layoutID===$activeLayoutElementGroup)|| (!$activeIDsSetNames.size && !$activeIDsElementGroups.size) || $activeIDsSetNames.has(id);

    $: active_class = active ? "" : "inactive";


     const transform_x_tween = tweened(position.x, {duration: 900})
    const transform_y_tween = tweened(position.y, {duration: 900})
    $: transform_x_tween.set(position.x)
    $: transform_y_tween.set(position.y)

</script>

<g class="nameG {id} {active_class}"
   id="{id}_name" rx="5px" transform={`translate(${$transform_x_tween}, ${$transform_y_tween})`} on:mouseenter={handleMouseOver}
   on:mouseleave={handleMouseOut} on:click={handleMouseClick} pointer-events="all">
    <rect fill={color} height="{size.height + 5}" rx="5px" stroke="none" width="{size.width + 5}" x="0" y="0" filter="saturate({$outlineSaturation/100.0})"></rect>
    <text class="set-name" fill="white">
        <tspan x="5" y="15"  font-weight="bold" font-size="16px" font-family="Arial, Helvetica, sans-serif">{text}</tspan>
    </text>
</g>

<style>

    .inactive {
        stroke: lightgrey;
        opacity: 0.1;
        transition: all 0.5s ease;
        fill-opacity: 0;
        fill: lightgray;
    }

    .nameG {
        cursor: default;
    }
        .set-name {
        font-family: Arial, Helvetica, sans-serif;
        font-weight: bold;
    }

</style>
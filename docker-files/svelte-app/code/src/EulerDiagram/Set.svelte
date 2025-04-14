<script>
    import {activeIDsElementGroups, activeIDsSetNames, activeLayoutElementGroup, outlineSaturation, fillOpacity} from "../store.js";

    export let classes;
    export let transform;
    export let id;
    export let data_sets;
    export let width;
    export let height;

    export let position;
    export let size;
    export let color

    export let inactive = false;
    export let ports
    export let hoveredElementGroup;
    export let layoutID

    import {tweened} from 'svelte/motion';

    const transform_x_tween = tweened(position.x, {duration: 900})
    const transform_y_tween = tweened(position.y, {duration: 900})
    const width_tween = tweened(size.width, {duration: 900})
    const height_tween = tweened(size.height, {duration: 900})
    $: transform_x_tween.set(position.x)
    $: transform_y_tween.set(position.y)
    $: width_tween.set(size.width)
    $: height_tween.set(size.height)

    $: active = ($activeIDsElementGroups.has(id) && layoutID === $activeLayoutElementGroup) || (!$activeIDsSetNames.size && !$activeIDsElementGroups.size) || $activeIDsSetNames.has(id);

    $: active_class = active ? "" : "inactive";

    $:{
        ports = {}
        ports["in_port"] = [$transform_x_tween, $transform_y_tween + $height_tween / 2]
        ports["out_port"] = [$transform_x_tween + $width_tween, $transform_y_tween + $height_tween / 2]

    }
</script>
<g class={active_class} id={id} transform={`translate(${$transform_x_tween}, ${$transform_y_tween})`}>
    <rect class="set-rect" data-sets="{data_sets}" x="0" y="0" stroke={color} fill={color} width={$width_tween}
          height={$height_tween} fill-opacity={$fillOpacity/100.0} filter="saturate({$outlineSaturation/100.0})"
          rx="5px">
    </rect>

</g>
<style>

    .inactive {
        stroke: lightgrey;
        opacity: 0.1;
        transition: all 0.5s ease;
        fill-opacity: 0;
        fill: lightgray;
    }
</style>
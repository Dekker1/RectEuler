<script>

    import iro from '@jaames/iro';
    import {onMount} from "svelte";
    import {clickOutside} from '../clickOutside.js';

    export let position;
    export let colorIDX;
    export let visible;
    export let colors;
    export let currentColor

    let colorPicker
    onMount(async () => {
        colorPicker = new iro.ColorPicker('#picker', {width: 150});
        colorPicker.on("color:change", colorChange);
    });

    function handleClickOutside(event) {
        visible = false;

    }

    function colorChange(color) {
        colors[colorIDX] = color.hexString
    }


    let display
    $:display = visible ? "block" : "none"

    $:{
        if (colorPicker) {
            colorPicker.color.hexString = currentColor
        }
    }
</script>

<div class="picker" id="picker"
     style="left: {position.x - 60}px; top:{position.y +20}px; display:{display}" use:clickOutside
     on:click_outside={handleClickOutside}
></div>


<style>
    .picker {
        position: absolute;
    }
</style>

<script>
    import {outlineSaturation, fillOpacity, enableOverlay, HoveringActive} from "../store.js";
    import {
        Button
    } from 'sveltestrap';

    function resetSettings() {
        $outlineSaturation = 100
        $fillOpacity = 5
        $enableOverlay = false
        $HoveringActive = true
    }
</script>
<div class="group-div">
    <label for="outlineSaturationSlider" class="block-label">Outline Saturation</label>
    <input type="range" min="0" max="100" class="slider" bind:value={$outlineSaturation} id="outlineSaturationSlider">
</div>
<div class="group-div">
    <label for="fillOpacitySlider" class="block-label">Fill Opacity</label>
    <input type="range" min="0" max="100" class="slider" bind:value={$fillOpacity} id="fillOpacitySlider">
</div>
<div class="group-div">
    <label for="enableOverlay" class="float-label">Enable Overlay</label>
    <input type="checkbox" id="enableOverlay" bind:checked={$enableOverlay}>
</div>
<div class="group-div">
    <label for="HoveringActive" class="float-label">Hovering active </label>
    <input type="checkbox" id="HoveringActive" bind:checked={$HoveringActive}>
</div>
<div class="group-div">
    <Button on:click={resetSettings}>Reset</Button>
</div>

<style>
    .block-label {
        display: block;
    }

    .slider {
        display: block;
    }

    .group-div {
        margin-top: 5px;
        margin-bottom: 5px;

    }

    .float-label {
        text-align: right;
        clear: both;
        float: left;
        margin-right: 15px;
    }
</style>
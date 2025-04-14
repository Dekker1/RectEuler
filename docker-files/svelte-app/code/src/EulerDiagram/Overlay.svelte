<script>
    export let classes;
    export let data_sets;
    export let d;
        import { fade } from 'svelte/transition';

</script>
<path transition:fade d={d} class={classes} data-sets={data_sets}></path>

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

    .intersectionOverlay {
        opacity: 0.1;
    }

</style>
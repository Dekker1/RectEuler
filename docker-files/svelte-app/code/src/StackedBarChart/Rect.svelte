<script>
    import {tweened} from 'svelte/motion';
    import {createEventDispatcher} from 'svelte'

    export let x;
    export let y;
    export let width;
    export let height;
    export let tweenOptions = undefined;
    export let key;
    export let group;

    let tweened_x = tweened(x, tweenOptions?.x);
    let tweened_y = tweened(y, tweenOptions?.y);
    let tweened_width = tweened(width, tweenOptions?.width);
    let tweened_height = tweened(height, tweenOptions?.height);

    $: tweened_x.set(x, tweenOptions?.x);
    $: tweened_y.set(y, tweenOptions?.y);
    $: tweened_width.set(width, tweenOptions?.width);
    $: tweened_height.set(height, tweenOptions?.height);

    const dispatch = createEventDispatcher()


    function handleMouseEnter(e) {

        dispatch("BarMouseEnter", {
            key: key,
            group: group,
            event: e
        })


    }

    function handleMouseLeave(e) {
        dispatch("BarMouseLeave", {
            key: key,
            group: group,
            event: e
        })


    }

    function handleClick(e) {
        dispatch("BarClick", {
            key: key,
            group: group,
            event: e
        })
    }


</script>

<rect
        x={$tweened_x}
        y={$tweened_y}
        width={$tweened_width}
        height={$tweened_height}
        on:mouseenter={handleMouseEnter}
        on:mouseleave={handleMouseLeave}
        on:click={handleClick}
        {...$$restProps}
        cursor="pointer"
        stroke="gray"


></rect>

<script>
    // 	Note: Due to REPL limitations, full responsiveness may not work here. Download the example from here or from the website (https://layercake.graphics/example/ColumnStacked) and run locally to get all features.
    import {LayerCake, Svg, flatten} from 'layercake';
    import {scaleBand, scaleOrdinal} from 'd3-scale';
    import {format, precisionFixed} from 'd3-format';
    import {stackOffsetExpand} from 'd3-shape';

    import Bar, {getStackExtents, stackOffsetSeparated} from './Bar.svelte';
    import AxisX from './AxisX.svelte';
    import AxisY from './AxisY.svelte';

    import {pivot} from './utils.js'

    export let data;
    export let groupBy;
    export let stackBy;
    export let reducer;

    export let stackKeys;
    export let keyColors;

    export let highlightColor;
    export let highlightGroup;
    export let external_extents
    export let layout;  // stacked, grouped, percent, or separated


    $: layout = 'stacked';
    $: options = layout === 'grouped' ? {layout: 'grouped'}
        : layout === 'stacked' ? {layout: 'stacked'}
            : layout === 'separated' ? {layout: 'stacked', offset: stackOffsetSeparated}
                : layout === 'percent' ? {layout: 'stacked', offset: stackOffsetExpand}
                    : {}

    export let formatTickY = d => format(layout === 'percent' ? `.0%` : `.${precisionFixed(d)}s`)(d);


    $:pivotData = pivot(data, groupBy, stackBy, reducer);

    let extents
    $: {
        if (external_extents) {
            extents = external_extents
        } else {
            extents = {y: getStackExtents(pivotData, options.offset, stackKeys)}

        }
    }


</script>


<div class="chart-container">
    <LayerCake

            {extents}
            custom={{pivotData:pivotData, groupBy:groupBy, stackBy:stackBy, highlightColor:highlightColor, highlightGroup:highlightGroup }}

            x={groupBy}
            xScale={scaleBand().paddingInner(0.1)}
            xDomain={data.map(d => d[groupBy])}

            y={d => d}

            r={d => d}
            rScale={scaleOrdinal()}
            rDomain={stackKeys}
            rRange={keyColors}

            padding={{ top: 20, bottom: 20, left: 30 }}
    >
        <Svg>
            <AxisX
                    gridlines={false}
                    {highlightGroup}
                    on:AxisXTickClick
            />
            <AxisY
                    ticks={4}
                    gridlines={true}
                    formatTick={formatTickY}
            />

            <Bar {groupBy} {stackBy} {...options} on:BarClick on:BarMouseLeave on:BarMouseEnter/>
        </Svg>
    </LayerCake>
</div>

<style>
    /*
        The wrapper div needs to have an explicit width and height in CSS.
        It can also be a flexbox child or CSS grid element.
        The point being it needs dimensions since the <LayerCake> element will
        expand to fill it.
    */
    .chart-container {
        width: 100%;
        height:150px;
        _background-color: rgba(0, 0, 0, .1);
    }
</style>
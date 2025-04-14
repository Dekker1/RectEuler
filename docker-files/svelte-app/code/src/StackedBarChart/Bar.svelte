<script context="module">
    import {extent, max} from 'd3-array';
    import {stackOffsetNone, stackOffsetExpand} from 'd3-shape';

    import Rect from './Rect.svelte';


    export function getGroupExtents(data, keys) {
        const values = data.flatMap(d => keys.map(key => d[key]));
        return extent(values);
    }

    export function getStackExtents(pivotData, offset, keys) {
        const stackData = stack().offset(offset).keys(keys)(pivotData);
        const extents = extent(stackData.flat(2));
        return extents
    }

    /**
     * Function to offset each layer by the maximum of the previous layer
     *   - see: https://observablehq.com/@mkfreeman/separated-bar-chart
     */
    export function stackOffsetSeparated(series, order) {
        // TODO: Determine way to pass in as option (curry?)
        const gap = 100;

        if (!((n = series.length) > 1)) return;

        // Standard series
        for (var i = 1, s0, s1 = series[order[0]], n, m = s1.length; i < n; ++i) {
            (s0 = s1), (s1 = series[order[i]]);
            let base = max(s0, d => d[1]) + gap; // here is where you calculate the maximum of the previous layer
            for (var j = 0; j < m; ++j) {
                // Set the height based on the data values, shifted up by the previous layer
                let diff = s1[j][1] - s1[j][0];
                s1[j][0] = base;
                s1[j][1] = base + diff;
            }
        }
    }
</script>

<script>
    import {getContext} from 'svelte';
    import {cubicInOut as easing} from 'svelte/easing';
    import {scaleBand} from 'd3-scale';
    import {stack} from 'd3-shape';


    const {xGet, xScale, yScale, yRange, rGet, rDomain, custom} = getContext('LayerCake');

    export let layout = 'stacked';  // stacked or grouped
    export let offset = stackOffsetNone;
    export let delay = 0;
    let stackData
    $: grouped = layout === 'grouped';

    $:stackData = stack().offset(offset).keys($rDomain)($custom.pivotData);


    $: chartData = grouped
        ? $custom.pivotData.flatMap(d => {
            return $rDomain.map(key => {

                return {
                    key,
                    values: [0, d[key]],
                    data: d
                }
            })
        })
        : stackData.flatMap(series => {
            return series.map(d => {
                if(!d[1]){
                    d[1] = d[0]
                }
                return {
                    key: series.key,
                    values: [d[0], d[1]],
                    data: d.data
                }
            })
        })



    $: x1Scale = scaleBand()
        .domain($rDomain)
        .range([0, $xScale.bandwidth()])
        .paddingInner(0.05)

    $: getDimensions = (item) => {
        return {
            x: $xGet(item.data) + (grouped ? x1Scale(item.key) : 0),
            y: $yScale(item.values[1]),
            width: grouped ? x1Scale.bandwidth() : $xScale.bandwidth(),
            height: $yScale(item.values[0]) - $yScale(item.values[1]),
        }
    }

    function getColor(key, item) {
        if ($custom.highlightGroup === item.toString()) {
            return $custom.highlightColor
        }
        return $rGet(key)
    }
</script>


<!-- TODO: Pass in top-level groupKey (or slice off of groupKeys) instead of using year directly -->
<g class="column-group">
    {#each chartData as item, i (`${item.data[$custom.groupBy]}-${item.key}`)}
        <Rect
                class='group-rect'
                fill={getColor(item.key, item.data[$custom.groupBy])}
                tweenOptions={{
				x: { easing, delay: grouped ? 0: delay },
				y: { easing, delay: grouped ? delay : 0 },
				width: { easing, delay: grouped ? 0 : delay },
				height: { easing, delay: grouped ? delay : 0 },
			}}
                key={item.key}
                group={item.data[$custom.groupBy]}
                on:BarClick
                on:BarMouseLeave
                on:BarMouseEnter
                {...getDimensions(item)}
                {...$$restProps}

        />
    {/each}
</g>
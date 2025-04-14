<script>
    import StackedBarChart from "../StackedBarChart/StackedBarChart.svelte";
    import {sum} from 'd3-array';
    import Switch from "../Switch/Switch.svelte";
    import {format, precisionFixed} from 'd3-format';
    import {getStackExtents} from "../StackedBarChart/Bar.svelte";

    export let data;
    export let layoutOptimizationStep
    let shapeList

    $:shapeList = []
    $:{
        console.log(data)
        shapeList = []
        for (const [idx, values] of data.entries()) {
            shapeList.push({step: idx, GAP: values.stats.GAP, MIPSOL_OBJ: values.stats.MIPSOL_OBJ, status: ""})
            shapeList = shapeList
        }
    }


    let multiValue = "GAP";
    const stackKeys = [""]
    const keyColors = ['lightgray'];

    $:reducer = items => sum(items, d => d[multiValue])

    function handleClick(e) {
        console.log(layoutOptimizationStep)
        layoutOptimizationStep = e.detail.group

    }

    let highlightColor = "darkgray"
    $:highlightGroup = layoutOptimizationStep + ""
    $:formatTickY = d => format(multiValue === 'GAP' ? `.0%` : `.${precisionFixed(d)}s`)(d);
    $: external_extents = multiValue === 'GAP' ? {y: [0, 1]} : null

</script>
<Switch bind:value={multiValue} label="" design="multi" options={['GAP', 'MIPSOL_OBJ']} fontSize={12}/>

<StackedBarChart data={shapeList} stackBy={"status"} groupBy={"step"} {reducer} {keyColors} {stackKeys} {highlightColor}
                 {highlightGroup} {external_extents} on:AxisXTickClick={handleClick} on:BarClick={handleClick}
                 {formatTickY}></StackedBarChart>
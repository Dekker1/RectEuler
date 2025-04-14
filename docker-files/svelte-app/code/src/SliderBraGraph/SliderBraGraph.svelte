<script>
    import * as d3 from 'd3'
    import * as d3slider from 'd3-simple-slider'

    import {apiData} from "../store.js";
    import Switch from "../Switch/Switch.svelte";

    let padding = 0.1;
    let height = 160;
    let margin = {top: 20, right: 50, bottom: 20, left: 40};
    let barheight = 125;
    let width = 800;
    let selectInput = "GAP"
    export let layoutID = 0

    let maxVal
    let minVal
    export let data

    $: minVal = selectInput === "GAP" ? 0 : d3.min(data, d => d[selectInput]);
    $: maxVal = d3.max(data, d => d[selectInput]);

    $: xDomain = data.map((d) => d[selectInput]);
    $: yDomain = selectInput === "GAP" ? [0, maxVal] : [0.9 * minVal, maxVal]


    $: xBand = d3
        .scaleBand()
        .domain(data.map(d => d[selectInput]))
        .range([margin.left, width - margin.right])
        .padding(padding);

    $: xLinear = d3.scaleLinear().domain([0, data.length - 1]).range([
        margin.left, width - margin.right]);

    $: yLinear = d3.scaleLinear()
        .domain(yDomain)
        .nice()
        .range([barheight - margin.bottom, margin.top]);

    $: innerWidth = width - (margin.left + margin.right);
    $: barWidth = innerWidth / data.length;


    function addSlider() {

        this.plot.append('g').attr('transform', `translate(0,${0})`).call(
            d3slider.sliderBottom(this.xLinear)
                .step(1)
                .ticks(4)
                .tickFormat(function (d, i) {
                    return d + 1;
                })
                .default(this.index)
                .on('onchange', (value) => {
                    this.updateIndex(value);
                }))

        d3.select('.track-overlay').attr('stroke-width', 150); // Ensure drag zone covers everything

    }

    const yTicks = [0, 5, 10, 15, 20];

</script>
<Switch bind:value={selectInput} label="Choose a theme" design="multi" options={['GAP', 'MIPSOL_OBJ']} fontSize={12}/>

<div class="chart" bind:clientWidth={width} bind:clientHeight={height}>
    <svg>
        <!-- y axis -->
        <g class="axis y-axis">
            {#each yTicks as tick}
                <g class="tick tick-{tick}" transform="translate(0, {yLinear(tick)})">
                    <line x2="100%"></line>
                    <text y="-4">{tick} {tick === 20 ? ' per 1,000 population' : ''}</text>
                </g>
            {/each}
        </g>
        <g transform="translate(0, 0)">
            <g class='bars'>
                {#each data as point, i}
                    <rect
                            x="{xLinear(i) + 2}"
                            y="{yLinear(point[selectInput])}"
                            width="{barWidth - 4}"
                            height="{yLinear(0) - yLinear(point[selectInput])}"
                    ></rect>
                {/each}
            </g>

        </g>
    </svg>
</div>

<style>
	h2 {
		text-align: center;
	}

	.chart {
		width: 100%;
		max-width: 500px;
		margin: 0 auto;
	}

	svg {
		position: relative;
		width: 100%;
		height: 200px;
	}

	.tick {
		font-family: Helvetica, Arial;
		font-size: .725em;
		font-weight: 200;
	}

	.tick line {
		stroke: #e2e2e2;
		stroke-dasharray: 2;
	}

	.tick text {
		fill: #ccc;
		text-anchor: start;
	}

	.tick.tick-0 line {
		stroke-dasharray: 0;
	}

	.x-axis .tick text {
		text-anchor: middle;
	}

	.bars rect {
		fill: #a11;
		stroke: none;
		opacity: 0.65;
	}
</style>
<script>
    import StackedBarChart from "../StackedBarChart/StackedBarChart.svelte";
    import {sum} from 'd3-array';
    import {hoveredDepth, hoveredLayoutIDs, hoveredStatus} from "../store.js";
    import {Col, Row} from "sveltestrap";
    import {format} from 'd3-format';

    export let data;
    export let layoutID
    let numberIntersections = 0
    let numberEmptyIntersections = 0
    let totalArea = 0
    let emptyArea = 0
    let shapeList
    $:{
        shapeList = []
        for (const [depth, intersections] of Object.entries(data.intersections)) {
            for (const intersection of intersections) {
                for (const shape of intersection.shapes) {
                    shapeList.push({depth: depth, status: shape.status, value: shape.area})
                    numberIntersections++
                    totalArea += shape.area
                    if (shape.status === "EmptyUnwantedIntersection") {
                        numberEmptyIntersections++
                        emptyArea += shape.area
                    }
                }
            }
        }
    }


    let multiValue = "number";
    const stackKeys = ["WantedFilledIntersection", "EmptyWantedIntersection", "EmptyUnwantedIntersection"]
    const keyColors = ['green', 'yellow', 'red'];

    let reducer
    $:{
        if (multiValue === "number") {
            reducer = items => items.length
        } else {
            reducer = items => sum(items, d => d.value)

        }
    }


    function handleMouseEnter(e) {

        $hoveredDepth = e.detail.group
        $hoveredStatus = e.detail.key
        $hoveredLayoutIDs = new Set(layoutID + "")
        console.log($hoveredLayoutIDs)

    }

    function handleMouseLeave(e) {

        $hoveredDepth = null
        $hoveredStatus = null
        $hoveredLayoutIDs = new Set()


    }

    let layout = "stacked";

</script>
<Row>
    <Col xs="4">
        <StackedBarChart data={shapeList} stackBy={"status"} groupBy={"depth"} {reducer} {keyColors} {stackKeys}
                         {layout}
                         on:BarMouseLeave={handleMouseLeave}
                         on:BarMouseEnter={handleMouseEnter}/>
    </Col>
    <Col xs="2">
        <label for="selectBarChartOptionIndividualStacked">Normalization:</label>
        <select bind:value={layout} id="selectBarChartOptionIndividualStacked">
            <option value="stacked">Stacked</option>
            <option value="percent">Percent</option>
        </select>
        <label for="selectBarChartOptionIndividual">Scaling:</label>
        <select bind:value={multiValue} id="selectBarChartOptionIndividual">
            <option value="area">Area</option>
            <option value="number">Number</option>

        </select>
    </Col>


    <Col xs="6">
        <div class="row align-items-start">
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <tr>
                        <th colspan="2">Diagrams</th>
                    </tr>
                    <tr>
                        <td>
                            #sets: {data.rects.length}
                        </td>
                        <td id="AllSetsNumberofSetsinVis"></td>
                    </tr>
                    <tr>
                        <td>
                            #zones: {numberIntersections}
                        </td>
                        <td id="AllSetsNumberofZonesVis"></td>
                    </tr>
                </table>
            </div>
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <th colspan="2">Empty Intersections</th>
                    <tr>
                        <td>
                            %area {format(".1%")(emptyArea / totalArea)}
                        </td>
                        <td id="AllSetsPercentEmptyArea"></td>
                    </tr>
                    <tr>
                        <td>
                            #intersection {numberEmptyIntersections}
                        </td>
                        <td id="AllSetsNumberofEmptyIntersections"></td>
                    </tr>


                </table>
            </div>
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <th colspan="2">Runtime</th>

                    <tr>
                        <td>
                            Subdiagrams {format(".1f")(data.stats.RUNTIME)}s
                        </td>
                        <td id="AllSetsFeasibleTimeTotal"></td>
                    </tr>

                </table>
            </div>
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <th colspan="2">MIP</th>

                    <tr>
                        <td>
                            Objective {format(".1f")(data.stats.MIPSOL_OBJ)}
                        </td>
                        <td id="AllSetsObjective"></td>
                    </tr>

                </table>
            </div>

        </div>
    </Col>
</Row>
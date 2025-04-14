<script>
    import StackedBarChart from "../StackedBarChart/StackedBarChart.svelte";
    import {hoveredDepth, hoveredLayoutIDs, hoveredStatus} from "../store.js";
    import {Col, Row} from "sveltestrap";
    import {sum} from 'd3-array';
	import { format } from 'd3-format';

    export let data;
    let shapeList
    $:{
        shapeList = []
        if (data) {
            for (const [layoutid, layout] of Object.entries(data)) {
                for (const [depth, intersections] of Object.entries(layout.intersections)) {
                    for (const intersection of intersections) {
                        for (const shape of intersection.shapes) {
                            shapeList.push({depth: depth, status: shape.status, value: shape.area})
                        }
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
        $hoveredLayoutIDs = new Set(Object.keys(data))

        console.log(data)

    }

    function handleMouseLeave(e) {

        $hoveredDepth = null
        $hoveredStatus = null
        $hoveredLayoutIDs = new Set()

    }

    let emptyArea
    let totalArea
    let numberEmptyIntersections
    let numberIntersections

    let sets

    let numberOfSetsInDiagram

    let numberOfElementsAbstract
    let numberOfElementgroupsAbstract
    let subdiagramRuntime
    let MIPObjective
    let timeSpendInfeasibleSols

    $:{
        numberIntersections = 0
        numberOfSetsInDiagram = 0
        emptyArea = 0
        totalArea = 0
        numberEmptyIntersections = 0
        numberOfElementsAbstract = 0
        numberOfElementgroupsAbstract = 0
        sets = new Set()
        subdiagramRuntime = 0
        MIPObjective = 0
        timeSpendInfeasibleSols = 0

        for (const sublayout of Object.values(data)) {
            for (const rect of Object.values(sublayout.rects)) {
                sets.add(rect.ID)
                numberOfSetsInDiagram++
            }
            for (const intersectionList of Object.values(sublayout.intersections)) {
                for (const intersection of intersectionList) {
                    for (const shape of intersection.shapes) {
                        numberIntersections++
                        totalArea += shape.area
                        if (shape.status === "EmptyUnwantedIntersection") {
                            numberEmptyIntersections++
                            emptyArea += shape.area
                        }
                    }
                }

            }
            for (const elementgroup of sublayout.element_groups) {
                numberOfElementgroupsAbstract++
                numberOfElementsAbstract += elementgroup.elements.length
            }
            subdiagramRuntime+= sublayout.stats.RUNTIME
            MIPObjective += sublayout.stats.MIPSOL_OBJ
            timeSpendInfeasibleSols= Math.max(sublayout.stats.timeSpendInfeasibleSols, timeSpendInfeasibleSols)
        }
    }


</script>

<Row>
    <Col xs="4">
        <label for="selectBarChartOption">Select scaling:</label>
        <select bind:value={multiValue} id="selectBarChartOption">
            <option value="area">Area</option>
            <option value="number">Number</option>

        </select>
        <StackedBarChart data={shapeList} stackBy={"status"} groupBy={"depth"} {reducer} {keyColors} {stackKeys}
                         on:BarMouseLeave={handleMouseLeave}
                         on:BarMouseEnter={handleMouseEnter}></StackedBarChart>
    </Col>
    <div class="col-8">
        <div class="row align-items-start">
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <tr>
                        <th colspan="2">Abstract Description</th>
                    </tr>
                    <tr>
                        <td>
                            #sets: {sets.size}
                        </td>
                        <td id="AllSetsNumberofSets"></td>
                    </tr>

                    <tr>
                        <td>
                            #elements: {numberOfElementsAbstract}
                        </td>
                        <td id="AllSetsNumberofElements"></td>
                    </tr>
                    <tr>
                        <td>
                            #zones: {numberOfElementgroupsAbstract}
                        </td>
                        <td id="AllSetsNumberofZonesAbstract"></td>
                    </tr>
                </table>
            </div>
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <tr>
                        <th colspan="2">Diagrams</th>
                    </tr>
                    <tr>
                        <td>
                            #sets: {numberOfSetsInDiagram}
                        </td>
                        <td id="AllSetsNumberofSetsinVis"></td>
                    </tr>
                    <tr>
                        <td>
                            #zones: {numberIntersections}
                        </td>
                        <td id="AllSetsNumberofZonesVis"></td>
                    </tr>
                    <tr>
                        <td>
                            #duplicated sets {numberOfSetsInDiagram - sets.size}
                        </td>
                        <td id="AllSetsNumberofDuplicatedSets"></td>
                    </tr>

                    <tr>
                        <td>
                            %duplicated sets
                        </td>
                        <td id="AllSetsPercentDuplicated"></td>
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
                            Infeasible {format(".1f")(timeSpendInfeasibleSols)}s
                        </td>
                        <td id="AllSetsTimeInfeasible"></td>
                    </tr>
                    <tr>
                        <td>
                            Subdiagrams {format(".1f")(subdiagramRuntime)}s
                        </td>
                        <td id="AllSetsFeasibleTimeTotal"></td>
                    </tr>
                    <tr>
                        <td>
                            Total {format(".1f")(timeSpendInfeasibleSols + subdiagramRuntime)}s
                        </td>
                        <td id="AllSetsTimeTotal"></td>
                    </tr>


                </table>
            </div>
            <div class="col-auto" style="padding-right: 0px;">
                <table>
                    <th colspan="2">MIP</th>

                    <tr>
                        <td>
                            Objective {format(".1f")(MIPObjective)}
                        </td>
                        <td id="AllSetsObjective"></td>
                    </tr>

                </table>
            </div>

        </div>
    </div>

</Row>



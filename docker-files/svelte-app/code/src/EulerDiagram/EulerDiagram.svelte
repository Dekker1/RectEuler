<script>

    import {onMount} from "svelte";
    import {activeTab} from "../store.js";
    import Set from "./Set.svelte";
    import ElementGroup from "./ElementGroup.svelte";
    import IntersectionOverlay from "./IntersectionOverlay.svelte";
    import {createEventDispatcher} from 'svelte';

    import {tweened} from "svelte/motion";
    import SetName from "./SetName.svelte";

    export let split;
    export let layoutID;


    export let previous;
    export let hoveredElementGroup;


    export let diagram;

    export let colors;

    let spacing = 30;

    export let w

    export let bbox;

    export let offset;


    let h;

    let g;
    const dispatch = createEventDispatcher();

    let ports = {}


    function getbox() {
        let minX = Infinity
        let minY = Infinity
        let maxX = -Infinity
        let maxY = -Infinity
        for (const [id, set] of Object.entries(diagram.rects)) {
            minX = Math.min(minX, set.position.x)
            minY = Math.min(minY, set.position.y)

            maxX = Math.max(maxX, set.position.x + set.size.width)
            maxY = Math.max(maxY, set.position.y + set.size.height)

        }
        let box = {x: minX, y: minY, right: maxX, bottom: maxY, width: maxX - minX, height: maxY - minY}

        for (const [id, set] of Object.entries(diagram.rects)) {
            set.position.x -= minX
            set.position.y -= minY

            ports[set.ID] = {
                "in_port": [set.position.x, set.position.y + set.size.height / 2],
                "out_port": [set.position.x + set.size.width,  set.position.y + set.size.height / 2]
            }

        }

        for (let element_group of diagram.element_groups) {
            element_group.position.x -= minX
            element_group.position.y -= minY

        }
        for (const [depth, intersections] of Object.entries(diagram.intersections)) {

            for (const intersection of intersections) {
                for (const shape of intersection.shapes) {
                    for (let point of shape.points) {
                        point[0] -= minX
                        point[1] -= minY
                    }
                }
            }
        }

        return box
    }

    let x_tween

    $:{
        diagram
        dispatch('sizeCalculated', {
            width: getbox().width,
            height: getbox().height,
            ID: parseInt(layoutID),
            ports : ports

        });
    }

    onMount(() => {
        /*
        console.log("recalc width")
        widths[layoutID] = getbox().width
        heights[layoutID] = getbox().height
        let sum = 0
        for (let i = 0; i < layoutID; i++) {
            sum += widths[i]
        }
        widths = widths
        //offset = sum
        offset = sum + layoutID * spacing
        x_tween = offset
        //x_tween.set(offset)

         */
        dispatch('sizeCalculated', {
            width: getbox().width,
            height: getbox().height,
            ID: parseInt(layoutID)

        });

    });


    //tweened(offset, {duration: 900})


    $:{


    }

    //x_tween.set(offset)


    function retnum(str) {
        let num = str.replace(/[^0-9]/g, '');
        return parseInt(num, 10);
    }


    $: {
        if ($activeTab == layoutID) {
            run()
        }

    }
    let blink;

    function run() {
        blink = "blink_me"
        setTimeout(() => {
            blink = ""
        }, 1000);


    }

    let setIDtoSetName
    $:{
        setIDtoSetName = {}
        for (const rect of diagram.rects) {
            setIDtoSetName[rect.ID] = rect.name.text
        }
    }

    let internal_ports = {}

    //export let ports

    /*
    $:{
        if (offset > -1) {
            ports[layoutID] = {}
            for (const [setID, p] of Object.entries(internal_ports)) {

                ports[setID] = {
                    "in_port": [p.in_port[0] + offset, p.in_port[1]],
                    "out_port": [p.out_port[0] + offset, p.out_port[1]]
                }
            }
            ports = ports
            internal_ports = internal_ports
        }


    }
*/
</script>

{#if offset > -1}
    <g id={"layout" + layoutID} transform="translate({offset}, 0)" bind:this={g} class="{blink}">

        <g class="overlayas">
            {#each Object.entries(diagram.intersections) as [depth, intersections]}
                {#each intersections as intersection}

                    {#each intersection.shapes as shape}
                        <IntersectionOverlay points={shape.points} status={shape.status}
                                             depth={depth} sets="{intersection.sets}" {layoutID}/>
                    {/each}
                {/each}

            {/each}
        </g>

        <g class="sets">
            {#each Object.values(diagram.rects) as setdata}

                <Set id={setdata.ID} position={setdata.position} size={setdata.size}
                     color="{colors[retnum(setdata.ID)]}" }
                     {layoutID}/>
            {/each}
        </g>

        <g class="elementGroups">
            {#each diagram.element_groups as elementGroup}
                <ElementGroup
                        id={elementGroup.id} position={elementGroup.position}
                        size={elementGroup.size} elements={elementGroup.elements}
                        containedin={elementGroup.containedin} colors="{colors}"
                        {setIDtoSetName} {layoutID}
                />
            {/each}
        </g>

        <g class="nameGroups">
            {#each Object.entries(diagram.rects) as [id, setdata]}
                <SetName position={setdata.position} size={setdata.name.size}
                         text={setdata.name.text} id={setdata.ID}
                         color="{colors[retnum(setdata.ID)]}" on:setNameClick
                         {layoutID}/>
            {/each}
        </g>


    </g>
{/if}

<style>

    .blink_me {
        animation: blinker 1s linear;
    }

    @keyframes blinker {
        50% {
            opacity: 0;
        }
    }
</style>
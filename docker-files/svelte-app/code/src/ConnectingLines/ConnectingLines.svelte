<script>

    import {activeIDsSetNames} from "../store.js";

    export let offsets
    export let ports;
    export let colors;
    let lines = []

    $:{
        if (false) {
            console.log(ports)
            lines = []
            let layoutIDs = Object.keys(ports).sort()
            for (let i = 0; i < layoutIDs.length - 1; i++) {
                let currentLayoutID = layoutIDs[i]
                let currentLayout = ports[currentLayoutID]
                for (const [setID, setPorts] of Object.entries(currentLayout)) {
                    let active = $activeIDsSetNames.has(setID);
                    if (!active) {
                        continue
                    }
                    let found = false
                    let offset = 1
                    while (!found && (i + offset) < layoutIDs.length) {
                        let nextLayoutID = layoutIDs[i + offset]
                        let nextLayout = ports[nextLayoutID]

                        if (setID in nextLayout) {
                            lines.push({
                                "start": currentLayout[setID].out_port,
                                "end": nextLayout[setID].in_port,
                                "ID": setID
                            })
                            found = true
                        }
                        offset++
                    }

                }

            }

            lines = lines
            console.log(lines)
        }

        if (Math.min(...offsets) > -1) {
            lines = []
            console.log(ports)
            for (let layoutID = 0; layoutID < ports.length - 1; layoutID++) {
                for (const [setID, setPorts] of Object.entries(ports[layoutID])) {
                    if (!$activeIDsSetNames.has(setID)) {
                        continue
                    }
                    let found = false
                    let offset = 1
                    while (!found && (layoutID + offset) < ports.length) {
                        let nextLayout = ports[layoutID + offset]
                        if (setID in nextLayout) {
                            let nextSetPorts = nextLayout[setID]
                            lines.push({
                                "start": [setPorts.out_port[0] + offsets[layoutID], setPorts.out_port[1]],
                                "end":  [nextSetPorts.in_port[0] + offsets[layoutID + offset], nextSetPorts.out_port[1]],
                                "ID": setID
                            })
                            found = true
                        }

                        offset++
                    }
                }
            }
            console.log(lines)

        }


    }

    function retnum(str) {
        let num = str.replace(/[^0-9]/g, '');
        return parseInt(num, 10);
    }

</script>


{#each lines as line}
    <line x1={line.start[0]} y1={line.start[1]} x2={line.end[0]} y2={line.end[1]} stroke-width="2" stroke={colors[retnum(line.ID)]}/>
{/each}
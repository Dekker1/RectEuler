<script>
    import {tooltip} from '../Tooltip/tooltip.js';
    import {activeIDs} from "../store.js";

    export let diam;
    export let x;
    export let y;
    export let id;
    export let name;

    export let color;



</script>

<circle class="encoding-circle" cx={x} cy={y} fill={color} title={name}
        r={diam/2}  use:tooltip></circle>
 {console.log(name)}
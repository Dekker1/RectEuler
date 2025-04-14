<script>
    export let data;
    export let head;
    export let firstcol;

    $:data
</script>

<div class="tablewrapper">

    <table>
        <thead>
        <tr>
            <th>Name</th>
            {#each head as d}
                <th>{d}</th>

            {/each}
        </tr>
        </thead>
        <tbody>
        {#each data as d, i}
            <tr>
                <td>{firstcol[i]}</td>
                {#each d as e}
                    <td>{e}</td>
                {/each}
            </tr>
        {/each}
        </tbody>
    </table>
</div>

<style>
    table {
        font-family: Arial, Helvetica, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }

    td, th {
        border: 1px solid #ddd;
        padding: 8px;
    }

    tr:nth-child(even) {
        background-color: #f2f2f2;
    }

    tr:hover {
        background-color: #ddd;
    }

    th {
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: left;
        background-color: #04AA6D;
        color: white;
    }

    .tablewrapper {
        max-height: 200px;
        overflow: scroll;
        width: 100%;
    }
</style>
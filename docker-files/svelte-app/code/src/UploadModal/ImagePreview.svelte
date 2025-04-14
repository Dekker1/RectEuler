<script>
    import {Col, Figure, Image} from 'sveltestrap';

    export let inputFile;

    let fileContent
    let reader = new FileReader();

    $:{
        reader.readAsDataURL(inputFile);
        reader.onload = e => {
            fileContent = e.target.result
        };
    }

    /**
     * Format bytes as human-readable text.
     *
     * @param bytes Number of bytes.
     * @param si True to use metric (SI) units, aka powers of 1000. False to use
     *           binary (IEC), aka powers of 1024.
     * @param dp Number of decimal places to display.
     *
     * @return Formatted string.
     */
    function humanFileSize(bytes, si = false, dp = 1) {
        const thresh = si ? 1000 : 1024;

        if (Math.abs(bytes) < thresh) {
            return bytes + ' B';
        }

        const units = si
            ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
            : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
        let u = -1;
        const r = 10 ** dp;

        do {
            bytes /= thresh;
            ++u;
        } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);


        return bytes.toFixed(dp) + ' ' + units[u];
    }

    export let removeFn


</script>
<div class="previwecontainer">
    <button id="x" on:click={removeFn}> X</button>

    <Figure>
        <Image thumbnail fluid class="imagepreviewthumb"
               style=" width:200px; height:200px;max-width: 200px;max-height: 200px;" alt="Preview"
               src={fileContent}/>
        <figcaption class="figure-caption">
            <p class="abc">{inputFile.name}</p>
            <p class="abc">{humanFileSize(inputFile.size)}</p>

        </figcaption>
    </Figure>
</div>

<style>
    .previwecontainer{
        position: relative;
    }
    .imagepreviewthumb {
        max-height: 200px;
        max-width: 200px;
    }

    .abc {
        margin: 0;
        max-width: 200px;
    }

    #x {
        position: absolute;
        background: red;
        color: white;
        top: 5px;
        right: 5px;
    }
</style>
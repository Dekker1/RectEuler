<script>
  import classnames from './utils.js';

  let className = '';
  export { className as class };
  export let active = false;

  $: classes = classnames(className, 'nav-item', active ? 'active' : false);
</script>

<li {...$$restProps} class={classes}>
  <slot />
</li>

<script>
  import classnames from './utils.js';

  let className = '';
  export { className as class };
  export let disabled = false;
  export let active = false;
  export let href = '#';

  $: classes = classnames(className, 'nav-link', {
    disabled,
    active
  });

  function handleClick(e) {
    if (disabled) {
      e.preventDefault();
      e.stopImmediatePropagation();
      return;
    }

    if (href === '#') {
      e.preventDefault();
    }
  }
</script>

<a {...$$restProps} {href} on:click on:click={handleClick} class={classes}  on:mouseenter on:mouseleave>
  <slot />
</a>

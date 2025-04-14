import {writable} from 'svelte/store';

export const count = writable(0);


export const apiData = writable(null);

export const layoutOptimizationStep = writable({});

export const activeIDsElementGroups = writable(new Set())
export const activeIDsSetNames = writable(new Set())

export const hoveredLayoutIDs = writable(new Set())
export const hoveredDepth = writable(null);
export const hoveredStatus = writable(null);

export const activeTab = writable(null);
export const ID = writable(null);

export const activeLayoutElementGroup = writable(null);

export const outlineSaturation = writable(100);
export const fillOpacity = writable(5);

export const enableOverlay = writable(false);
export const HoveringActive = writable(true);



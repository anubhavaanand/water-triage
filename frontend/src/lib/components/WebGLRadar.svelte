<script>
    import { onMount } from 'svelte';
    import { initMap } from '../webgl/engine.js';

    onMount(async () => {
        // Run the engine
        await initMap();
    });
</script>

<!-- The visible WebGL Canvas -->
<canvas id="webgl" class="absolute inset-0 w-full h-full z-0 pointer-events-auto" style="content-visibility: auto;"></canvas>

<!-- Dummy DOM to satisfy engine.js event listeners without crashing -->
<div id="dummy-dom" style="display: none;">
    <div id="kpi-total"></div><div id="kpi-crit"></div><div id="kpi-high"></div><div id="kpi-low"></div><div id="stat-chip"></div>
    <div id="btn-toggle-mesh"></div><div id="simulator-drawer"></div><div id="btn-mode-globe"></div><div id="btn-mode-regional"></div>
    <div id="hero-overlay"></div><div id="panel-left"></div><div id="panel-right"></div><div id="btn-hero-explore"></div>
    <div id="brand-home"></div><div id="btn-camera-reset"></div><div id="tooltip"></div><div id="queue-list"></div>
    <div id="queue-search"></div><div id="queue-count"></div><div id="btn-clear-search"></div>
    <div id="rex-river-name"></div><div id="rex-river-length"></div><div id="rex-stat-stations"></div><div id="rex-stat-crit"></div>
    <div id="rex-stat-score"></div><div id="rex-stat-hazard"></div><div id="rex-threat-box"></div><div id="rex-corridor-badge"></div>
    <div id="btn-rex-focus"></div><div id="btn-rex-reset"></div><div id="btn-toggle-sim"></div><div id="btn-close-sim"></div>
    <input id="range-arsenic" type="range"><input id="range-fluoride" type="range"><input id="range-ecoli" type="range">
    <input id="range-nitrate" type="range"><input id="range-iron" type="range">
    <div id="val-arsenic"></div><div id="val-fluoride"></div><div id="val-ecoli"></div><div id="val-nitrate"></div><div id="val-iron"></div>
    <div id="sim-score-num"></div><div id="sim-badge"></div><div id="sim-rec-text"></div>
    <div id="detail-modal"></div><div id="btn-close-modal"></div><div id="modal-village-name"></div><div id="modal-village-meta"></div>
    <div id="modal-readings-body"></div><div id="modal-recurrence-info"></div><div id="modal-intervention-info"></div>
    <div id="dossier-modal"></div><div id="btn-project-info"></div><div id="btn-close-dossier"></div><div id="btn-export-station"></div>
    <div id="fps-val"></div><div id="tt-title"></div><div id="tt-sub"></div><div id="tt-score"></div><div id="ui-layer"></div>
    <!-- The engine also expects elements matching '.filter-chip' but document.querySelectorAll is safe -->
</div>

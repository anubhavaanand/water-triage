<script>
    let { navigate } = $props();
    let meta = $state(null);
    let loading = $state(true);
    let error = $state(null);

    $effect(() => {
        fetch('/api/meta')
            .then(r => r.ok ? r.json() : Promise.reject())
            .catch(() => fetch(`${import.meta.env.BASE_URL}meta.json`).then(r => r.json()))
            .then(data => {
                meta = data;
                loading = false;
            })
            .catch(err => {
                error = err.message;
                loading = false;
            });
    });
</script>

<div class="section" style="padding-top: 0;">
  <div class="container">
    <header class="row-between" style="margin-bottom: var(--gap-xl); padding-bottom: var(--gap-lg); border-bottom: 2px solid var(--color-fg);">
      <h1 class="h1">Overview</h1>
      <button class="btn btn-ghost btn-arrow" onclick={() => navigate('a')}>Back to Queue</button>
    </header>

    {#if loading}
      <div class="callout" style="text-align: center; margin-top: var(--gap-xl);">Loading overview data…</div>
    {:else if error}
      <div class="error-box">Error: {error}</div>
    {:else if meta}
      <div class="grid-4" style="margin-bottom: var(--gap-xl);">
        <div class="sketch-box" style="text-align: center;">
          <div class="stat">
            <span class="stat-num" style="color: var(--color-fg);">{meta.corpus?.samples?.toLocaleString() || '1,741'}</span>
            <div class="stat-label">Scored Samples</div>
          </div>
        </div>
        <div class="sketch-box" style="text-align: center;">
          <div class="stat">
            <span class="stat-num" style="color: var(--color-critical);">{meta.bands?.Critical || 89}</span>
            <div class="stat-label">Critical<br><span class="badge badge-critical">≥ 75</span></div>
          </div>
        </div>
        <div class="sketch-box" style="text-align: center;">
          <div class="stat">
            <span class="stat-num" style="color: var(--color-high);">{meta.bands?.High || 392}</span>
            <div class="stat-label">High<br><span class="badge badge-high">50–74</span></div>
          </div>
        </div>
        <div class="sketch-box" style="text-align: center;">
          <div class="stat">
            <span class="stat-num" style="color: var(--color-low);">{meta.corpus?.historical_events_distinct?.toLocaleString() || 'N/A'}</span>
            <div class="stat-label">Historical Events</div>
          </div>
        </div>
      </div>

      {#if meta.critical_concentration}
        <div class="callout" style="margin-bottom: var(--gap-xl); text-align: center;">
          {meta.critical_concentration.single_parameter_iron_critical} of {meta.critical_concentration.total_critical} Critical samples are single-parameter iron results from {meta.critical_concentration.district} district
        </div>
      {/if}

      {#if meta.state_comparison}
        <div class="grid-2" style="margin-top: var(--gap-xl);">
          {#each meta.state_comparison as stateData}
            <div class="sketch-box">
              <h2 class="h3" style="margin-bottom: var(--gap-md); display: flex; justify-content: space-between; border-bottom: 1px dashed var(--color-border); padding-bottom: var(--gap-sm);">
                {stateData.state}
                <span class="meta">N={stateData.samples}</span>
              </h2>
              <div class="stack" style="gap: var(--gap-lg);">
                <div>
                  <div class="meta" style="margin-bottom: 4px;">Mean Composite Risk Score</div>
                  <div class="h1" style="font-size: clamp(36px, 5vw, 60px); color: {stateData.mean_crs > 15 ? 'var(--color-critical)' : 'var(--color-fg)'};">
                    {stateData.mean_crs.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div class="meta" style="margin-bottom: 4px;">Critical Samples</div>
                  <div class="h1" style="font-size: clamp(36px, 5vw, 60px);">
                    {stateData.critical_count}
                  </div>
                  <p class="meta" style="margin-top: 8px;">
                    {(stateData.critical_share_of_all_critical * 100).toFixed(1)}% of all critical samples.
                  </p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>
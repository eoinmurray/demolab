// Development-only controls. A fragment restores one article atomically; it never reaches builds.
function demolabPreviewOptions(runs, choice) {
  // A pinned run that is currently newest uses the same displayed option as Latest.
  const value = runs.length && choice === 'run:' + runs[0].id ? 'latest' : choice;
  const options = [['latest', 'Latest' + (runs.length ? ' — ' + runs[0].id : '')],
    ...runs.slice(1).map(run => ['run:' + run.id, run.id])];
  if (!options.some(option => option[0] === value)) options.push([value, value.replace(/^run:/, '')]);
  return {options, value};
}

(() => {
  const article = decodeURIComponent(location.pathname).replace(/\/$/, '').split('/').pop().replace(/\.html$/, '');
  const automaticReload = history.state?.demolabPreviewReload === location.href;
  if (automaticReload) history.replaceState({...history.state, demolabPreviewReload: null}, '');
  let token, panel, fields, message, activity, state, structure = '', initialized = false, desired = {};
  let anchor = '', sending = 0, reloadPending = false, updating = false, localError = '';
  let requests = Promise.resolve();
  const controls = new Map();
  const node = (tag, text, parent) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (parent) parent.append(element);
    return element;
  };

  function readFragment() {
    const parts = location.hash.slice(1).split('&');
    anchor = parts[0] && !parts[0].includes('=') ? parts.shift() : '';
    const choices = {};
    for (const [key, value] of new URLSearchParams(parts.join('&'))) {
      if (!key.startsWith('run.')) continue;
      const input = key.slice(4);
      if (Object.hasOwn(choices, input)) throw new Error('Duplicate input in preview URL: ' + input);
      choices[input] = value;
    }
    return choices;
  }

  function writeFragment(push = false) {
    const params = new URLSearchParams();
    for (const [key, choice] of Object.entries(desired)) params.set('run.' + key, choice);
    const fragment = [anchor, params.toString()].filter(Boolean).join('&');
    const url = location.pathname + location.search + (fragment ? '#' + fragment : '');
    if (url !== location.pathname + location.search + location.hash) {
      history[push ? 'pushState' : 'replaceState'](history.state, '', url);
    }
  }

  function mount() {
    if (panel) return;
    const style = node('style');
    style.textContent = `
      .entry-meta:has(+ .demolab-preview:not([hidden])) {margin-bottom:0}
      .demolab-preview {font:inherit;font-size:var(--fs-small,.85rem);color:var(--muted,#666);margin:1.25rem 0;display:flex;flex-wrap:wrap;align-items:baseline;gap:.35rem 1rem}
      .demolab-preview:not([hidden]) + * {margin-top:0}
      .demolab-preview-inputs {display:flex;flex-wrap:wrap;gap:.35rem 1rem;min-width:0}
      .demolab-preview label {display:flex;align-items:baseline;gap:.4rem;min-width:0;max-width:100%}
      .demolab-preview label span {overflow-wrap:anywhere}
      .demolab-preview select {font:inherit;color:var(--ink,#1a1a1a);background:var(--paper,#fff);border:0;border-bottom:1px solid var(--rule-strong,#d8d5cd);border-radius:0;padding:.12rem 0;min-width:0;max-width:100%;cursor:pointer}
      .demolab-preview button {font:inherit;color:inherit;background:none;border:0;padding:0;text-decoration:underline;text-underline-offset:2px;cursor:pointer;white-space:nowrap}
      .demolab-preview :is(select,button):focus-visible {outline:2px solid var(--ink,#1a1a1a);outline-offset:3px}
      .demolab-preview-actions {display:flex;align-items:center;gap:.75rem;white-space:nowrap}
      .demolab-preview [role=status] {display:inline-block;width:8ch;min-height:1.6em;line-height:1.6}
      .demolab-preview [role=alert] {flex-basis:100%;white-space:pre-wrap;overflow-wrap:anywhere;max-height:12em;overflow:auto}
      .demolab-preview [role=alert]:empty {display:none}
      .demolab-preview .error {color:var(--ink,#1a1a1a);border-left:2px solid currentColor;padding-left:.6rem}
      .demolab-preview[hidden] {display:none}
    `;
    document.head.append(style);
    panel = node('section');
    panel.className = 'demolab-preview';
    panel.setAttribute('aria-label', 'Preview data sources');
    fields = node('div', undefined, panel);
    fields.className = 'demolab-preview-inputs';
    const actions = node('div', undefined, panel);
    actions.className = 'demolab-preview-actions';
    const reset = node('button', 'Reset to default', actions);
    reset.type = 'button';
    reset.onclick = () => {
      desired = {};
      writeFragment(true);
      send(true);
    };
    activity = node('span', '', actions);
    activity.setAttribute('role', 'status');
    activity.setAttribute('aria-live', 'polite');
    message = node('div', '', panel);
    message.setAttribute('role', 'alert');
    const metadata = document.querySelector('.entry-meta');
    if (metadata) metadata.after(panel);
    else document.body.prepend(panel); // failed first build: still allow recovery
  }

  function showError(error) {
    mount();
    panel.hidden = false;
    activity.textContent = '';
    message.className = 'error';
    message.textContent = error + '\nShowing the last successful build.';
  }
  window.__demolabPreviewError = showError;
  window.__demolabPreviewReload = () => {
    if (sending) { reloadPending = true; return; }
    // An automatic reload adopts the shared preview, rather than fighting another tab's URL.
    // Manual refresh and Back/Forward still restore the fragment as requested.
    history.replaceState({...history.state, demolabPreviewReload: location.href}, '');
    location.reload();
  };

  function send(reset = false) {
    const selections = {...desired};
    localError = '';
    sending++;
    render();
    requests = requests.then(async () => {
      try {
        const response = await fetch('/__preview', {
          method: 'POST', headers: {'Content-Type': 'application/json', 'X-Demolab-Token': token},
          body: JSON.stringify({action: 'article', article, selections, reset})
        });
        if (!response.ok) {
          const result = await response.json().catch(() => ({}));
          throw new Error(result.error || 'Preview request rejected');
        }
      } catch (error) { localError = String(error); }
      finally {
        sending--;
        await update();
        render();
        if (!sending && reloadPending) {
          reloadPending = false;
          if (!localError) window.__demolabPreviewReload();
        }
      }
    });
  }

  function render() {
    if (!state || state.disabled) return;
    const inputs = state.articles[article] || [];
    if (!inputs.length && !state.error && !localError) {
      if (panel) panel.hidden = true;
      return;
    }
    mount();
    panel.hidden = false;
    const nextStructure = JSON.stringify(inputs);
    if (structure !== nextStructure) {
      structure = nextStructure;
      fields.replaceChildren();
      controls.clear();
      inputs.forEach(input => {
        const label = node('label', undefined, fields);
        if (inputs.length > 1) node('span', input.key, label);
        const select = node('select', undefined, label);
        select.setAttribute('aria-label', input.key + ' run');
        select.onchange = () => {
          desired[input.key] = select.value;
          writeFragment(true);
          send();
        };
        controls.set(input.key, {select, options: ''});
      });
    }
    inputs.forEach(input => {
      const control = controls.get(input.key);
      const runs = state.runs.filter(run => run.experiment === input.experiment);
      const choice = desired[input.key] || 'latest';
      const {options, value} = demolabPreviewOptions(runs, choice);
      const signature = JSON.stringify(options);
      if (signature !== control.options) {
        control.select.replaceChildren();
        options.forEach(([value, text]) => { const option = node('option', text, control.select); option.value = value; });
        control.options = signature;
      }
      control.select.value = value;
    });
    if (localError || state.error) showError(localError || (state.stale ? 'Sources unavailable.\n' : '') + state.error);
    else {
      message.className = '';
      message.textContent = '';
      activity.textContent = sending || state.busy ? 'Updating…' : '';
    }
  }

  async function update() {
    if (updating) return;
    updating = true;
    try {
      const response = await fetch('/__preview', {cache: 'no-store'});
      if (!response.ok) throw new Error('Cannot read preview status');
      state = await response.json();
      if (state.disabled) { if (panel) panel.hidden = true; return; }
      token = state.token;
      if (!initialized && state.articles[article]?.length) {
        initialized = true;
        desired = readFragment();
        if (automaticReload) {
          desired = {...(state.selections[article] || {})};
          // Migrate previously saved Published/default choices to the new Latest default.
          for (const key of Object.keys(desired)) if (desired[key] === 'published') delete desired[key];
          writeFragment();
        }
        const inputs = state.articles[article];
        const current = state.selections[article] || {};
        if (Object.keys(desired).some(key => !inputs.some(input => input.key === key)) ||
            inputs.some(input => (desired[input.key] || 'latest') !== (current[input.key] || 'latest'))) send();
        if (anchor) document.getElementById(decodeURIComponent(anchor))?.scrollIntoView();
      }
      render();
    } catch (error) { localError = String(error); showError(localError); }
    finally { updating = false; }
  }

  window.addEventListener('hashchange', () => {
    if (!initialized) return;
    try {
      const choices = readFragment();
      // Heading links retain the selections while still scrolling to their section.
      if (anchor && !Object.keys(choices).length) { writeFragment(); return; }
      desired = choices;
      send();
    } catch (error) { localError = String(error); showError(localError); }
  });
  update();
  setInterval(update, 1000);
})();

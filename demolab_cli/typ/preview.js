// Injected by the development server only. The generated site never contains this control.
(() => {
  const article = decodeURIComponent(location.pathname).replace(/\/$/, '').split('/').pop().replace(/\.html$/, '');
  let token = '', panel, fields, message, summary, structure = '', lastState;
  const controls = new Map();
  const node = (tag, text, parent) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (parent) parent.append(element);
    return element;
  };
  function mount() {
    if (panel) return;
    const style = node('style');
    style.textContent = `
      .demolab-preview {font:14px/1.5 system-ui,sans-serif;border:1px solid #8888;border-radius:8px;padding:12px;margin:16px 0;background:#f5f7f6;color:#172d2b}
      .demolab-preview summary {cursor:pointer;font-weight:600;overflow-wrap:anywhere}
      .demolab-preview fieldset {border:1px solid #8886;margin:12px 0;min-width:0}
      .demolab-preview label {display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:8px 0}
      .demolab-preview label span {min-width:100px;overflow-wrap:anywhere}
      .demolab-preview select {flex:1;min-width:0;max-width:100%;padding:5px;font:inherit}
      .demolab-preview small {display:block;flex-basis:100%;overflow-wrap:anywhere}
      .demolab-preview button {font:inherit;padding:5px 10px;margin:8px 8px 0 0;cursor:pointer}
      .demolab-preview [role=status] {white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0;max-height:16em;overflow:auto}
      .demolab-preview .error {color:#9f2323}
      .demolab-preview a {margin-right:12px}
    `;
    document.head.append(style);
    panel = node('details');
    panel.className = 'demolab-preview';
    panel.open = true;
    summary = node('summary', 'Data sources', panel);
    fields = node('div', undefined, panel);
    message = node('div', '', panel);
    message.setAttribute('role', 'status');
    message.setAttribute('aria-live', 'polite');
    const refresh = node('button', 'Refresh sources', panel);
    refresh.type = 'button';
    refresh.onclick = () => send({action: 'refresh'});
    const reset = node('button', 'Reset all selections to Latest', panel);
    reset.type = 'button';
    reset.onclick = () => send({action: 'reset'});
    document.body.prepend(panel);
  }
  async function send(payload) {
    try {
      message.textContent = 'Change queued; displayed results stay unchanged until compilation succeeds.';
      const response = await fetch('/__preview', {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-Demolab-Token': token},
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error((await response.json()).error || 'Preview request rejected');
      await update();
    } catch (error) { showError(String(error)); }
  }
  function showError(error) {
    mount();
    panel.hidden = false;
    panel.open = true;
    lastState = undefined;
    message.className = 'error';
    message.textContent = error + '\nDisplayed results may be from the last successful build. Choose another input or fix the source.';
  }
  window.__demolabPreviewError = showError;
  function render(state) {
    token = state.token;
    const inputs = state.articles[article] || [];
    if (!inputs.length && !state.error && !state.busy) {
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
      const groups = new Map();
      inputs.forEach(input => {
        let group = groups.get(input.group);
        if (!group) {
          group = node('fieldset', undefined, fields);
          node('legend', input.group || 'Inputs', group);
          groups.set(input.group, group);
        }
        const label = node('label', undefined, group);
        node('span', input.experiment, label);
        const select = node('select', undefined, label);
        select.setAttribute('aria-label', input.key + ' run');
        const active = node('small', '', label);
        select.onchange = () => send({action: 'select', article, key: input.key, choice: select.value});
        controls.set(input.key, {select, active, options: ''});
      });
      if (!inputs.length) {
        Object.keys(state.articles).forEach(id => {
          const link = node('a', id, fields);
          link.href = '/' + encodeURIComponent(id);
        });
      }
    }
    const rendered = [];
    inputs.forEach(input => {
      const control = controls.get(input.key);
      const runs = state.runs.filter(run => run.experiment === input.experiment);
      const choice = (state.selections[article] || {})[input.key] || 'latest';
      const options = [
        ['latest', 'Latest' + (runs.length ? ' — ' + runs[0].id : ' — no available runs')],
        ['published', 'Published/default'],
        ...runs.map(run => ['run:' + run.id, run.label + ' — ' + run.id])
      ];
      if (!options.some(option => option[0] === choice)) options.push([choice, 'Unavailable — ' + choice.replace(/^run:/, '')]);
      const signature = JSON.stringify(options);
      if (signature !== control.options) {
        control.select.replaceChildren();
        options.forEach(([value, label]) => { const option = node('option', label, control.select); option.value = value; });
        control.options = signature;
      }
      control.select.value = choice;
      const active = (state.rendered[article] || {})[input.key] || 'not yet built in this session';
      control.active.textContent = 'Rendered: ' + active;
      rendered.push(input.key + ': ' + active);
    });
    summary.textContent = 'Data sources' + (rendered.length ? ' — ' + rendered.join(' · ') : '') + (state.busy ? ' — building…' : '');
    summary.title = rendered.join('\n');
    if (state.error) showError((state.stale ? 'Source catalogue is stale.\n' : '') + state.error);
    else {
      message.className = '';
      message.textContent = state.busy ? 'Building… displayed results have not changed yet.' : 'Preview only. Ordinary builds use authored defaults.';
    }
  }
  async function update() {
    try {
      const response = await fetch('/__preview', {cache: 'no-store'});
      if (!response.ok) throw new Error('Cannot read preview status');
      const state = await response.json();
      if (state.disabled) { if (panel) panel.hidden = true; return; }
      const signature = JSON.stringify(state);
      if (lastState !== signature) { render(state); lastState = signature; }
    } catch (error) { showError(String(error)); }
  }
  update();
  setInterval(update, 1000);
})();

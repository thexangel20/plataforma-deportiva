(() => {
  const search = document.querySelector('#catalog-search');
  const picks = new Set();
  const tray = document.querySelector('#compare-picks');
  const refreshPicks = () => {
    if (!tray) return;
    tray.hidden = picks.size === 0;
    document.querySelector('#pick-count').textContent = picks.size;
    const fields = document.querySelector('#pick-inputs');
    fields.replaceChildren();
    for (const id of picks) {
      const input = document.createElement('input');
      input.type = 'hidden'; input.name = 'deporte'; input.value = id;
      fields.append(input);
    }
    document.querySelectorAll('[data-pick]').forEach(input => {
      input.checked = picks.has(input.dataset.pick);
      input.disabled = picks.size >= 3 && !input.checked;
    });
    tray.querySelector('button').disabled = picks.size < 2;
  };
  document.addEventListener('change', event => {
    if (event.target.matches('[data-pick]')) {
      if (event.target.checked && picks.size < 3) picks.add(event.target.dataset.pick);
      else picks.delete(event.target.dataset.pick);
      refreshPicks();
    }
  });
  document.querySelector('#clear-picks')?.addEventListener('click', () => {picks.clear(); refreshPicks();});
  if (search) {
    let timer, controller;
    const update = async () => {
      controller?.abort();
      controller = new AbortController();
      const params = new URLSearchParams(new FormData(search));
      const count = document.querySelector('#results-count');
      count.textContent = 'Buscando…';
      try {
        const response = await fetch('/catalogo/resultados?' + params, {signal: controller.signal});
        if (!response.ok) throw new Error('No se pudo buscar');
        const data = await response.json();
        document.querySelector('#catalog-results').innerHTML = data.html;
        count.textContent = data.count + (data.count === 1 ? ' deporte para explorar' : ' deportes para explorar');
        history.replaceState(null, '', '/?' + params + '#catalogo');
        refreshPicks();
      } catch (error) {
        if (error.name !== 'AbortError') count.textContent = 'No pudimos actualizar la búsqueda. Intenta nuevamente.';
      }
    };
    search.addEventListener('submit', event => { event.preventDefault(); clearTimeout(timer); update(); });
    search.querySelector('[name=q]').addEventListener('input', () => {clearTimeout(timer); timer = setTimeout(update, 250);});
    search.querySelector('select').addEventListener('change', () => {clearTimeout(timer); update();});
  }
})();

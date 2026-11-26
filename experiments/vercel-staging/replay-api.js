/* Static staging only. Application API requests never leave this origin. */
(() => {
  'use strict';
  const json = (body, status = 200) => new Response(JSON.stringify(body), {
    status, headers: {'Content-Type': 'application/json; charset=utf-8'},
  });
  const unavailable = () => json({error: 'This recording is unavailable in staging.'}, 404);
  const raw = (file, options) => window.fetch('/_recorded/' + file, options);

  window.StagingReplay = Object.freeze({
    async fetch(input, options = {}) {
      if (options.method && options.method.toUpperCase() !== 'GET') {
        return json({error: 'Recorded staging is read-only.'}, 405);
      }
      const url = new URL(input, location.origin);
      if (url.origin !== location.origin) return unavailable();
      const params = url.searchParams;
      if (url.pathname === '/api/config') return raw('config.json', options);
      if (url.pathname === '/api/saved-result') return raw('saved-result.json', options);
      if (url.pathname === '/api/briefs') {
        const response = await raw('briefs.json', options);
        if (!response.ok) return response;
        const query = (params.get('q') || '').trim().toLowerCase();
        const offset = Math.max(0, Number(params.get('offset')) || 0);
        const {briefs} = await response.json();
        return json({briefs: briefs.filter(brief => String(brief.archived) === (params.get('archived') || '0')
          && brief.title.toLowerCase().includes(query)).slice(offset, offset + 30)});
      }
      const brief = /^\/api\/briefs\/([a-f0-9]{32})$/.exec(url.pathname);
      if (brief && !params.has('version')) {
        const response = await raw('briefs/' + brief[1] + '.json', options);
        return response.status === 404 ? unavailable() : response;
      }
      if (url.pathname === '/api/evidence-table') {
        const response = await raw('table-routes.json', options);
        if (!response.ok) return response;
        const routes = await response.json();
        const key = params.get('index') + ':' + params.get('chunk_id');
        return Object.hasOwn(routes, key) ? window.fetch(routes[key], options) : unavailable();
      }
      return unavailable();
    },
  });
})();

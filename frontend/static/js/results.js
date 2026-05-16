function renderizarResultadosDinamicos(pagesArray) {
    if (!pagesArray || !pagesArray.length) return;

    const container = document.getElementById('results-container');
    if (!container) return;

    // Reiniciar vista
    ['overview', 'architecture', 'business-logic', 'onboarding-path', 'setup', 'testing', 'docker', 'repo-map'].forEach(slug => {
        const el = document.getElementById(`module-${slug}`);
        if (el) el.style.display = 'none';
    });
    container.style.display = 'block';

    pagesArray.sort((a, b) => (a.order || 0) - (b.order || 0));

    pagesArray.forEach(page => {
        const moduleEl = document.getElementById(`module-${page.slug}`);
        if (!moduleEl) return;
        moduleEl.style.display = 'block';

        // Procesar Markdown usando la librería oficial y montarlo en memoria
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = page.markdown ? marked.parse(page.markdown) : '';

        // Extraer título principal (H1) si existe
        const h1 = tempDiv.querySelector('h1');
        const h1Title = h1 ? h1.textContent : page.title;

        switch (page.slug) {
            case 'overview':        llenarOverview(tempDiv, h1Title); break;
            case 'architecture':    llenarArchitecture(tempDiv); break;
            case 'business-logic':  llenarBusinessLogic(tempDiv); break;
            case 'onboarding-path': llenarOnboardingPath(tempDiv); break;
            // Módulos deterministas (Python backend) asumen page.data
            case 'setup':           llenarSetup(page.data); break;
            case 'testing':         llenarTesting(page.data); break;
            case 'docker':          llenarDocker(page.data); break;
            case 'repo-map':        llenarRepoMap(page.data); break;
        }
    });

    activarAcordeones();
}

// Busca un <h2> que contenga alguna de las keywords y extrae todo el HTML 
// hermano siguiente hasta topar con otro <h2> o <h1>.
function extraerSeccionHTML(tempDiv, keywords) {
    const h2s = Array.from(tempDiv.querySelectorAll('h2'));
    for (let h2 of h2s) {
        const title = h2.textContent.toLowerCase();
        if (keywords.some(kw => title.includes(kw))) {
            let html = '';
            let curr = h2.nextElementSibling;
            while (curr && curr.tagName !== 'H2' && curr.tagName !== 'H1') {
                html += curr.outerHTML;
                curr = curr.nextElementSibling;
            }
            return html.trim() || '<span style="color:#8b949e;font-style:italic;">Sección vacía.</span>';
        }
    }
    return '';
}

// Helpers de Inyección DOM
function inyectar(id, html, fallback = false) {
    const el = document.getElementById(id);
    if (!el) return;
    if (html) {
        el.innerHTML = html;
        el.style.display = 'block';
        const label = el.previousElementSibling;
        if (label && label.classList.contains('section-label')) label.style.display = 'block';
    } else {
        el.style.display = fallback ? 'block' : 'none';
        if (!html && fallback) el.innerHTML = '<span style="color:#8b949e;font-style:italic;">No detectado.</span>';
        const label = el.previousElementSibling;
        if (label && label.classList.contains('section-label')) label.style.display = fallback ? 'block' : 'none';
    }
}

// Llenado por módulo (IA)

function llenarOverview(tempDiv, h1Title) {
    document.getElementById('res-project-name').textContent = h1Title || '—';
    const summary = extraerSeccionHTML(tempDiv, ['summary', 'resumen', 'description']);
    inyectar('res-project-desc', summary, true);

    const techs = extraerSeccionHTML(tempDiv, ['technologies', 'tecnologías', 'stack']);
    inyectar('res-metrics', techs);

    document.getElementById('res-analysis-date').textContent = new Date().toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' });
    const statusEl = document.getElementById('res-repo-status');
    if (statusEl && !statusEl.textContent.trim()) statusEl.textContent = 'Activo';
}

function llenarArchitecture(tempDiv) {
    inyectar('res-arch-style', extraerSeccionHTML(tempDiv, ['general', 'description', 'descripción']));
    inyectar('res-arch-patterns', extraerSeccionHTML(tempDiv, ['components', 'componentes', 'patterns']));
    inyectar('res-arch-flow', extraerSeccionHTML(tempDiv, ['flow', 'flujo']), true);
}

function llenarBusinessLogic(tempDiv) {
    inyectar('res-biz-core', extraerSeccionHTML(tempDiv, ['flow', 'flujo', 'core']), true);
    inyectar('res-biz-rules', extraerSeccionHTML(tempDiv, ['decisions', 'decisiones', 'rules']));
    inyectar('res-biz-entities', ''); // Ocultar
}

function llenarOnboardingPath(tempDiv) {
    inyectar('res-path-order', extraerSeccionHTML(tempDiv, ['reading order', 'orden de lectura', 'order']), true);
    inyectar('res-path-concepts', extraerSeccionHTML(tempDiv, ['key concepts', 'conceptos clave']));
    inyectar('res-path-checklist', extraerSeccionHTML(tempDiv, ['checklist', 'commit']));
}

// Llenado Módulos Deterministas (Python Backend JSON)

function llenarSetup(data) {
    if (!data) return;
    inyectar('res-setup-prereqs', asListHTML(data.prerequisites));
    inyectar('res-setup-env', asListHTML(data.env_vars));
    const cmds = document.getElementById('res-setup-commands');
    if (data.commands) cmds.innerHTML = `<pre style="margin:0;overflow-x:auto;"><code>${escapeHtml(data.commands)}</code></pre>`;
    else cmds.style.display = 'none';
}

function llenarTesting(data) {
    if (!data) return;
    inyectar('res-test-happy', asListHTML(data.happy_path));
    inyectar('res-test-edge', asListHTML(data.edge_cases));
    inyectar('res-test-security', asListHTML(data.security_cases));
    inyectar('res-test-privacy', data.privacy_notes);
}

function llenarDocker(data) {
    if (!data) return;
    inyectar('res-docker-infra', data.infra_explanation);
    if (data.dockerfile) document.getElementById('res-docker-file').innerHTML = `<pre style="margin:0;overflow-x:auto;"><code>${escapeHtml(data.dockerfile)}</code></pre>`;
    if (data.docker_compose) document.getElementById('res-docker-compose').innerHTML = `<pre style="margin:0;overflow-x:auto;"><code>${escapeHtml(data.docker_compose)}</code></pre>`;
}

function llenarRepoMap(data) {
    if (!data) return;
    inyectar('res-map-entry', asListHTML(data.entry_points));
    inyectar('res-map-table', buildFileTable(data.file_table));
    inyectar('res-map-graph', buildDepsTable(data.dependencies));
}

// Interfaz y Helpers

function activarAcordeones() {
    document.querySelectorAll('.accordion-header').forEach(header => {
        const nuevo = header.cloneNode(true);
        header.parentNode.replaceChild(nuevo, header);
        nuevo.addEventListener('click', function () {
            this.classList.toggle('collapsed');
            this.nextElementSibling.classList.toggle('hidden');
        });
    });
}

function asListHTML(arr) {
    if (!arr || !arr.length) return '';
    return `<ul>${arr.map(i => `<li>${i}</li>`).join('')}</ul>`;
}

function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function buildFileTable(rows) {
    if (!rows || !rows.length) return '';
    const header = `<tr style="background:#1e2430;"><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Archivo</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Impacto</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Descripción</th></tr>`;
    const body = rows.map((r, i) => `<tr style="${i % 2 ? 'background:#292f38;' : ''}"><td style="padding:9px 14px;font-family:monospace;color:#79c0ff;">${r.file}</td><td style="padding:9px 14px;">${impactBadge(r.impact)}</td><td style="padding:9px 14px;">${r.description}</td></tr>`).join('');
    return `<table style="width:100%;border-collapse:collapse;">${header}${body}</table>`;
}

function buildDepsTable(rows) {
    if (!rows || !rows.length) return '';
    const header = `<tr style="background:#1e2430;"><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Origen</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Importa a →</th></tr>`;
    const body = rows.map((r, i) => `<tr style="${i % 2 ? 'background:#292f38;' : ''}"><td style="padding:9px 14px;font-family:monospace;color:#79c0ff;">${r.source}</td><td style="padding:9px 14px;font-family:monospace;color:#c9d1d9;">${r.imports}</td></tr>`).join('');
    return `<table style="width:100%;border-collapse:collapse;">${header}${body}</table>`;
}

function impactBadge(level) {
    const map = { 'Alta': { bg:'#1b4b27', color:'#4caf50', border:'#2e7d32' }, 'Media': { bg:'#3d2e00', color:'#f0ad4e', border:'#7a5c00' }, 'Baja': { bg:'#1a1f2e', color:'#8b949e', border:'#30363d' } };
    const s = map[level] || map['Baja'];
    return `<span style="background:${s.bg};color:${s.color};border:1px solid ${s.border};padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">${level}</span>`;
}
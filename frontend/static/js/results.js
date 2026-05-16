function renderizarResultadosDinamicos(pagesArray) {
    if (!pagesArray || !pagesArray.length) return;

    const container = document.getElementById('results-container');
    if (!container) return;

    // Reiniciar vista
    ['overview', 'architecture', 'business-logic', 'onboarding-path'].forEach(slug => {
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

        switch (page.slug) {
            case 'overview':        llenarOverview(tempDiv); break;
            case 'architecture':    llenarArchitecture(tempDiv); break;
            case 'business-logic':  llenarBusinessLogic(tempDiv); break;
            case 'onboarding-path': llenarOnboardingPath(tempDiv); break;
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

function llenarOverview(tempDiv) {
    const summary = extraerSeccionHTML(tempDiv, ['summary', 'resumen', 'description']);
    inyectar('res-overview-desc', summary, true);

    const techs = extraerSeccionHTML(tempDiv, ['technologies', 'tecnologías', 'stack']);
    inyectar('res-overview-tech', techs);
}

function llenarArchitecture(tempDiv) {
    const desc = extraerSeccionHTML(tempDiv, ['general', 'description', 'descripción']);
    inyectar('res-arch-desc', desc, true);
    
    const components = extraerSeccionHTML(tempDiv, ['components', 'componentes', 'patterns']);
    inyectar('res-arch-components', components);
}

function llenarBusinessLogic(tempDiv) {
    const flow = extraerSeccionHTML(tempDiv, ['flow', 'flujo', 'core']);
    inyectar('res-biz-flow', flow, true);
    
    const decisions = extraerSeccionHTML(tempDiv, ['decisions', 'decisiones', 'rules']);
    inyectar('res-biz-decisions', decisions);
}

function llenarOnboardingPath(tempDiv) {
    const order = extraerSeccionHTML(tempDiv, ['reading order', 'orden de lectura', 'order']);
    inyectar('res-path-order', order, true);
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
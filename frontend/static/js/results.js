function renderDynamicResults(pagesArray) {
    if (!pagesArray || !pagesArray.length) return;

    const container = document.getElementById('results-container');
    if (!container) return;

    // Reset view
    ['overview', 'architecture', 'business-logic', 'onboarding-path', 'security-audit', 'technical-debt'].forEach(slug => {
        const el = document.getElementById(`module-${slug}`);
        if (el) el.style.display = 'none';
    });
    container.style.display = 'block';

    pagesArray.sort((a, b) => (a.order || 0) - (b.order || 0));

    pagesArray.forEach(page => {
        const moduleEl = document.getElementById(`module-${page.slug}`);
        if (!moduleEl) return;
        moduleEl.style.display = 'block';

        // Process Markdown using the official library and mount it in memory
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = page.markdown ? marked.parse(page.markdown) : '';

        switch (page.slug) {
            case 'overview':        fillOverview(tempDiv); break;
            case 'architecture':    fillArchitecture(tempDiv); break;
            case 'business-logic':  fillBusinessLogic(tempDiv); break;
            case 'onboarding-path': fillOnboardingPath(tempDiv); break;
            case 'security-audit':  fillSecurityAudit(tempDiv); break;
            case 'technical-debt':  fillTechnicalDebt(tempDiv); break;
        }
    });

    activateAccordions();

    // Transform and render Mermaid.js diagrams
    setTimeout(async () => {
        if (window.mermaid) {
            mermaid.initialize({
                startOnLoad: false,
                theme: 'dark',
                securityLevel: 'loose'
            });
            
            document.querySelectorAll('code.language-mermaid').forEach(el => {
                const pre = el.parentElement;
                const mermaidCode = el.textContent.trim();
                
                // Create container for the diagram
                const container = document.createElement('div');
                container.style.marginTop = '20px';
                container.style.marginBottom = '20px';
                
                try {
                    // Validate basic Mermaid syntax
                    if (!mermaidCode || mermaidCode.length < 10) {
                        throw new Error('Empty or invalid Mermaid code');
                    }
                    
                    const div = document.createElement('div');
                    div.className = 'mermaid';
                    div.textContent = mermaidCode;
                    container.appendChild(div);
                    pre.parentNode.replaceChild(container, pre);
                } catch (err) {
                    console.warn('Invalid Mermaid syntax detected:', err);
                    // Show a friendly error message instead of the error bomb
                    container.innerHTML = `
                        <div style="background: #2d1b1b; border: 1px solid #5a2828; border-radius: 6px; padding: 16px; color: #ff6b6b;">
                            <strong>⚠️ Diagram Generation Error</strong>
                            <p style="margin: 8px 0 0 0; color: #c9d1d9; font-size: 0.9em;">
                                The AI-generated diagram contains syntax errors. The raw Mermaid code is shown below:
                            </p>
                            <pre style="background: #0d1117; padding: 12px; border-radius: 4px; margin-top: 12px; overflow-x: auto; color: #8b949e; font-size: 0.85em;"><code>${escapeHtml(mermaidCode)}</code></pre>
                        </div>
                    `;
                    pre.parentNode.replaceChild(container, pre);
                }
            });
            
            // Render all valid Mermaid diagrams
            try {
                await mermaid.run({ querySelector: '.mermaid' });
            } catch (e) {
                console.error('Error rendering Mermaid diagrams:', e);
                // Replace failed diagrams with error messages
                document.querySelectorAll('.mermaid').forEach(el => {
                    if (el.getAttribute('data-processed') !== 'true') {
                        const mermaidCode = el.textContent;
                        el.innerHTML = `
                            <div style="background: #2d1b1b; border: 1px solid #5a2828; border-radius: 6px; padding: 16px; color: #ff6b6b;">
                                <strong>⚠️ Diagram Rendering Error</strong>
                                <p style="margin: 8px 0 0 0; color: #c9d1d9; font-size: 0.9em;">
                                    Unable to render the diagram. Please check the syntax below:
                                </p>
                                <pre style="background: #0d1117; padding: 12px; border-radius: 4px; margin-top: 12px; overflow-x: auto; color: #8b949e; font-size: 0.85em;"><code>${escapeHtml(mermaidCode)}</code></pre>
                            </div>
                        `;
                    }
                });
            }
        }
    }, 100);
}

// Searches for a <h*> that contains any of the keywords and extracts all
// sibling HTML until hitting another header of the same or higher level.
function extractSectionHTML(tempDiv, keywords) {
    const headers = Array.from(tempDiv.querySelectorAll('h1, h2, h3, h4'));
    
    for (let h of headers) {
        const title = h.textContent.toLowerCase().trim();
        
        // Check if any keyword matches
        if (keywords.some(kw => title.includes(kw.toLowerCase()))) {
            let html = '';
            let curr = h.nextElementSibling;
            const headerLevel = parseInt(h.tagName.substring(1));
            
            // Extract content until we hit another header of same or higher level
            while (curr) {
                const currTag = curr.tagName;
                
                // Stop if we hit a header of same or higher level
                if (['H1', 'H2', 'H3', 'H4'].includes(currTag)) {
                    const currLevel = parseInt(currTag.substring(1));
                    if (currLevel <= headerLevel) {
                        break;
                    }
                }
                
                html += curr.outerHTML;
                curr = curr.nextElementSibling;
            }
            
            const trimmedHtml = html.trim();
            return trimmedHtml || '<span style="color:#8b949e;font-style:italic;">Empty section.</span>';
        }
    }
    return '';
}

// DOM Injection Helpers
function inject(id, html, fallback = false) {
    const el = document.getElementById(id);
    if (!el) return;
    if (html) {
        el.innerHTML = html;
        el.style.display = 'block';
        const label = el.previousElementSibling;
        if (label && label.classList.contains('section-label')) label.style.display = 'block';
    } else {
        el.style.display = fallback ? 'block' : 'none';
        if (!html && fallback) el.innerHTML = '<span style="color:#8b949e;font-style:italic;">Not detected.</span>';
        const label = el.previousElementSibling;
        if (label && label.classList.contains('section-label')) label.style.display = fallback ? 'block' : 'none';
    }
}

// Module fill functions (AI-driven)

function fillOverview(tempDiv) {
    let summary = extractSectionHTML(tempDiv, ['summary', 'description', 'general', 'overview']);
    let techs = extractSectionHTML(tempDiv, ['technologies', 'stack', 'tech']);
    if (!summary && !techs) summary = tempDiv.innerHTML;
    inject('res-overview-desc', summary, true);
    inject('res-overview-tech', techs);
}

function fillArchitecture(tempDiv) {
    // Extract sections in order
    let desc = extractSectionHTML(tempDiv, ['overview', 'description']);
    let components = extractSectionHTML(tempDiv, ['main components', 'components', 'key components']);
    let diagram = extractSectionHTML(tempDiv, ['diagram', 'architecture diagram']);
    
    // Remove mermaid diagrams from description to avoid duplication
    if (desc) {
        const tempDescDiv = document.createElement('div');
        tempDescDiv.innerHTML = desc;
        // Remove any mermaid code blocks from description
        tempDescDiv.querySelectorAll('pre code.language-mermaid, .mermaid').forEach(el => {
            const pre = el.closest('pre');
            if (pre) pre.remove();
            else el.remove();
        });
        desc = tempDescDiv.innerHTML.trim();
    }
    
    // If no specific sections found, use all content but separate diagrams
    if (!desc && !components && !diagram) {
        const tempAllDiv = document.createElement('div');
        tempAllDiv.innerHTML = tempDiv.innerHTML;
        
        // Extract diagrams
        const diagramElements = tempAllDiv.querySelectorAll('pre code.language-mermaid, .mermaid');
        let diagramHTML = '';
        diagramElements.forEach(el => {
            const pre = el.closest('pre');
            if (pre) {
                diagramHTML += pre.outerHTML;
                pre.remove();
            } else {
                diagramHTML += el.outerHTML;
                el.remove();
            }
        });
        
        desc = tempAllDiv.innerHTML.trim();
        diagram = diagramHTML || diagram;
    }
    
    inject('res-arch-desc', desc, true);
    inject('res-arch-components', components);
    inject('res-arch-diagram', diagram);
}

function fillBusinessLogic(tempDiv) {
    let flow = extractSectionHTML(tempDiv, ['core processes', 'flow', 'core', 'logic', 'business flow', 'process']);
    let decisions = extractSectionHTML(tempDiv, ['business rules', 'decisions', 'rules', 'entities']);
    
    // If no specific sections, try to split content intelligently
    if (!flow && !decisions) {
        const allContent = tempDiv.innerHTML;
        // Check if there's any content at all
        if (allContent && allContent.trim().length > 0) {
            flow = allContent;
        }
    }
    
    inject('res-biz-flow', flow, true);
    inject('res-biz-decisions', decisions);
}

function fillOnboardingPath(tempDiv) {
    let order = extractSectionHTML(tempDiv, ['reading order', 'recommended order', 'order', 'path', 'guide', 'onboarding', 'getting started']);
    
    // If no specific section, use all content
    if (!order) {
        const allContent = tempDiv.innerHTML;
        if (allContent && allContent.trim().length > 0) {
            order = allContent;
        }
    }
    
    inject('res-path-order', order, true);
}

function fillSecurityAudit(tempDiv) {
    let vuln = extractSectionHTML(tempDiv, ['vulnerabilities', 'security issues', 'owasp', 'secrets', 'security', 'findings', 'detected']);
    let rec = extractSectionHTML(tempDiv, ['recommendations', 'mitigation', 'fixes', 'solutions', 'best practices']);
    
    // If no specific sections, try to use all content for vulnerabilities
    if (!vuln && !rec) {
        const allContent = tempDiv.innerHTML;
        if (allContent && allContent.trim().length > 0) {
            vuln = allContent;
        }
    }
    
    inject('res-sec-vuln', vuln, true);
    inject('res-sec-rec', rec);
}

function fillTechnicalDebt(tempDiv) {
    let issues = extractSectionHTML(tempDiv, ['debt', 'issues', 'anti-patterns', 'practices']);
    let refactor = extractSectionHTML(tempDiv, ['refactor', 'suggestions']);
    if (!issues && !refactor) issues = tempDiv.innerHTML;
    inject('res-debt-issues', issues, true);
    inject('res-debt-refactor', refactor);
}

// Interface and Helpers

function activateAccordions() {
    document.querySelectorAll('.accordion-header').forEach(header => {
        const clone = header.cloneNode(true);
        header.parentNode.replaceChild(clone, header);
        clone.addEventListener('click', function () {
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
    const header = `<tr style="background:#1e2430;"><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">File</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Impact</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Description</th></tr>`;
    const body = rows.map((r, i) => `<tr style="${i % 2 ? 'background:#292f38;' : ''}"><td style="padding:9px 14px;font-family:monospace;color:#79c0ff;">${r.file}</td><td style="padding:9px 14px;">${impactBadge(r.impact)}</td><td style="padding:9px 14px;">${r.description}</td></tr>`).join('');
    return `<table style="width:100%;border-collapse:collapse;">${header}${body}</table>`;
}

function buildDepsTable(rows) {
    if (!rows || !rows.length) return '';
    const header = `<tr style="background:#1e2430;"><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Source</th><th style="padding:9px 14px;text-align:left;color:#8b949e;border-bottom:1px solid #484f58;">Imports →</th></tr>`;
    const body = rows.map((r, i) => `<tr style="${i % 2 ? 'background:#292f38;' : ''}"><td style="padding:9px 14px;font-family:monospace;color:#79c0ff;">${r.source}</td><td style="padding:9px 14px;font-family:monospace;color:#c9d1d9;">${r.imports}</td></tr>`).join('');
    return `<table style="width:100%;border-collapse:collapse;">${header}${body}</table>`;
}

function impactBadge(level) {
    const map = { 'High': { bg:'#1b4b27', color:'#4caf50', border:'#2e7d32' }, 'Medium': { bg:'#3d2e00', color:'#f0ad4e', border:'#7a5c00' }, 'Low': { bg:'#1a1f2e', color:'#8b949e', border:'#30363d' } };
    const s = map[level] || map['Low'];
    return `<span style="background:${s.bg};color:${s.color};border:1px solid ${s.border};padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">${level}</span>`;
}
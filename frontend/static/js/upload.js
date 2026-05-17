// select all button
document.addEventListener('DOMContentLoaded', () => {
    const selectAllBtn = document.getElementById('select-all-btn');
    let allSelected = false;

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            allSelected = !allSelected;
            const checkboxes = document.querySelectorAll('input[name="filtros"]');
            
            checkboxes.forEach(cb => {
                cb.checked = allSelected;
            });

            selectAllBtn.innerHTML = allSelected
                ? 'Deselect All <span class="check-icon">✖</span>'
                : 'Select All <span class="check-icon">✔</span>';
            
            // Actualizar visibilidad del botón de descarga
            updateDownloadButtonVisibility();
        });
    }

    // Manejar checkbox de documentación completa
    const fullDocCheckbox = document.getElementById('full-doc-checkbox');
    const downloadSection = document.getElementById('download-section');
    
    if (fullDocCheckbox && downloadSection) {
        fullDocCheckbox.addEventListener('change', () => {
            updateDownloadButtonVisibility();
        });
    }

    // Manejar botón de descarga
    const downloadBtn = document.getElementById('download-docs-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownloadDocumentation);
    }
});

// Función para mostrar/ocultar el botón de descarga
function updateDownloadButtonVisibility() {
    const fullDocCheckbox = document.getElementById('full-doc-checkbox');
    const downloadSection = document.getElementById('download-section');
    
    if (fullDocCheckbox && downloadSection) {
        if (fullDocCheckbox.checked) {
            downloadSection.style.display = 'block';
        } else {
            downloadSection.style.display = 'none';
        }
    }
}

// Función para manejar la descarga de documentación
async function handleDownloadDocumentation() {
    const btn = document.getElementById('download-docs-btn');
    const token = document.getElementById('github-token').value;
    let repoUrl = document.getElementById('repo-url').value;
    
    // Validar inputs
    if (!token) {
        alert('⚠️ Please enter your GitHub token first');
        return;
    }
    
    if (!repoUrl) {
        alert('⚠️ Please enter a repository URL first');
        return;
    }
    
    // Limpiar URL si es necesario
    let repository = repoUrl;
    if (repoUrl.includes('github.com')) {
        const urlParts = repoUrl.split('github.com/');
        if (urlParts.length > 1) {
            repository = urlParts[1].replace('.git', '');
        }
    }
    
    // Deshabilitar botón y mostrar estado de carga
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span style="margin-right: 8px;">⏳</span> Generating Documentation...';
    
    // Preparar payload con todos los filtros activados
    const payload = {
        github_token: token,
        repository: repository,
        branch: document.getElementById('branch').value,
        filters: {
            "overview": true,
            "architecture": true,
            "business-logic": true,
            "onboarding-path": true,
            "security-audit": true,
            "technical-debt": true
        },
        extensions: null
    };
    
    console.log('📥 Downloading documentation for:', repository);
    
    try {
        const response = await fetch('http://localhost:8000/download-docs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            // Obtener el blob del response
            const blob = await response.blob();
            
            // Extraer nombre del archivo del header Content-Disposition
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'ODST_Technical_Documentation.md';
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/"/g, '');
                }
            }
            
            // Crear URL temporal y descargar
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Limpiar
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('✅ Documentation downloaded successfully:', filename);
            
            // Mostrar mensaje de éxito
            btn.innerHTML = '<span style="margin-right: 8px;">✅</span> Downloaded Successfully!';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }, 3000);
            
        } else {
            // Manejar error
            let errorMessage = 'Failed to generate documentation';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                errorMessage = `Server error: ${response.status}`;
            }
            
            console.error('❌ Download failed:', errorMessage);
            alert(`❌ Error: ${errorMessage}`);
            
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
        
    } catch (error) {
        console.error('❌ Download error:', error);
        alert(`❌ Error downloading documentation: ${error.message}`);
        
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// analyze repository
document.getElementById('odst-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Hide button and show status console
    const btn = document.getElementById('analyze-btn');
    const consoleDiv = document.getElementById('status-console');
    
    btn.disabled = true;
    btn.innerHTML = "Processing...";
    consoleDiv.style.display = "block";


    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    
    step1.className = "step active"; step1.innerHTML = "[Active] Connecting to Extraction API...";
    step2.className = "step waiting"; step2.innerHTML = "[Waiting] Waiting for files...";
    step3.className = "step waiting"; step3.innerHTML = "[Waiting] Agent workflow...";

    // Generate the filter object that the backend expects
    const filtrosSeleccionados = {
        "overview": false,
        "architecture": false,
        "business-logic": false,
        "onboarding-path": false,
        "security-audit": false,
        "technical-debt": false
    };

    const checkboxes = document.querySelectorAll('input[name="filtros"]');
    checkboxes.forEach((cb) => {
        if (filtrosSeleccionados.hasOwnProperty(cb.value)) {
            filtrosSeleccionados[cb.value] = cb.checked;
        }
    });

    // Collect input data
    const token = document.getElementById('github-token').value;
    let repoUrl = document.getElementById('repo-url').value;
    let repository = repoUrl;

    // Clean URL if user pasted the full GitHub link
    if (repoUrl.includes('github.com')) {
        const urlParts = repoUrl.split('github.com/');
        if (urlParts.length > 1) {
            repository = urlParts[1].replace('.git', '');
        }
    }

    // Prepare final Payload for Andre and the agents
    const payloadParaElBackend = {
        github_token: token,
        repository: repository,
        branch: document.getElementById('branch').value,
        filters: filtrosSeleccionados, 
        extensions: null
    };

    console.log("JSON Payload to send:", payloadParaElBackend);

    try {
        console.log("🚀 Sending request to backend...");
        console.log("Payload:", payloadParaElBackend);
        
        // Call to Andre's FastAPI server
        const response = await fetch('http://localhost:8000/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payloadParaElBackend)
        });

        console.log("📡 Response status:", response.status);
        
        let data;
        try {
            data = await response.json();
            console.log("📦 Response data:", data);
        } catch (jsonError) {
            console.error("❌ Failed to parse JSON response:", jsonError);
            throw new Error(`Server returned invalid JSON (Status ${response.status})`);
        }

        if (response.ok && data.status === 'success') {
            // extraction success
            console.log("✅ Extraction successful!");
            step1.className = "step done";
            step1.innerHTML = `[Done] Repository cloned and processed.`;
            
            step2.className = "step done";
            step2.innerHTML = "[Done] Compressed Context JSON generated.";

            step3.className = "step done";
            step3.innerHTML = "[Done] Documentation generated successfully.";
            btn.innerHTML = "Analysis Completed";
            btn.disabled = false; // Reactivate in case they want to analyze another
            
            // Render the actual results using the pages array from the backend
            if (data.frontend_docs && data.frontend_docs.pages) {
                // Filtra solo los módulos que fueron seleccionados
                const filteredPages = data.frontend_docs.pages.filter(page => filtrosSeleccionados[page.slug]);
                renderizarResultadosDinamicos(filteredPages);
            }

        } else {
            // Handle error response
            let errorMessage = "Unknown error in extraction";
            let errorDetails = "";
            
            if (data.detail) {
                // Try to parse detail if it's JSON
                try {
                    const detailObj = typeof data.detail === 'string' ? JSON.parse(data.detail) : data.detail;
                    errorMessage = detailObj.error_message || data.detail;
                    errorDetails = detailObj.traceback || "";
                    console.error("❌ Error details:", detailObj);
                } catch {
                    errorMessage = data.detail;
                    console.error("❌ Error detail:", data.detail);
                }
            } else if (data.message) {
                errorMessage = data.message;
                console.error("❌ Error message:", data.message);
            }
            
            // Log full error for debugging
            console.error("❌ Full error data:", data);
            
            throw new Error(errorMessage);
        }

    } catch (error) {
        console.error('❌ Pipeline Error:', error);
        
        // Show detailed error in the UI
        step1.className = "step waiting";
        step1.style.color = "#ff4444";
        
        let errorDisplay = error.message;
        
        // Truncate very long error messages for UI
        if (errorDisplay.length > 200) {
            errorDisplay = errorDisplay.substring(0, 200) + "... (ver consola para detalles completos)";
        }
        
        step1.innerHTML = `[Error] ${errorDisplay}`;
        
        // Show additional error info in step 2
        step2.className = "step waiting";
        step2.style.color = "#ff8844";
        step2.innerHTML = "[Info] Revisa la consola del navegador (F12) para más detalles";
        
        // Show troubleshooting tips in step 3
        step3.className = "step waiting";
        step3.style.color = "#ffaa44";
        step3.innerHTML = "[Tip] Verifica: token válido, repositorio existe, permisos correctos";
        
        btn.innerHTML = "Retry";
        btn.disabled = false;
        
        // Log helpful debugging info
        console.log("\n🔍 DEBUGGING INFORMATION:");
        console.log("Repository:", repository);
        console.log("Token length:", token.length);
        console.log("Token starts with:", token.substring(0, 4) + "...");
        console.log("Filters:", filtrosSeleccionados);
        console.log("\n💡 TROUBLESHOOTING TIPS:");
        console.log("1. Verify your GitHub token is valid and has repo access");
        console.log("2. Check that the repository exists and is accessible");
        console.log("3. Ensure the backend server is running on http://localhost:8000");
        console.log("4. Check the backend console for detailed error logs");
    }
});

// render results (markdown)
function renderDynamicResults(pagesArray) {
    const container = document.getElementById('results-container');
    
    // Avoid errors if the function is called in a view where the container doesn't exist
    if (!container) return;

    container.innerHTML = '';

    pagesArray.forEach(page => {
        const tabDiv = document.createElement('div');
        tabDiv.className = 'markdown-tab accordion-item';
        
        // Assign title and inject raw Markdown
        // (You'll need Marked.js in your HTML to convert text to real HTML)
        tabDiv.innerHTML = `
            <button class="accordion-header">${page.title}</button>
            <div class="accordion-content">
                <div class="markdown-body">
                    <pre>${page.markdown}</pre>
                </div>
            </div>
        `;
        
        container.appendChild(tabDiv);
    });
}
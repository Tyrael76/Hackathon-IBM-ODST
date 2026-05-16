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
        });
    }
});

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
        "setup": false,
        "testing": false,
        "docker": false,
        "repo-map": false
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
        // Call to Andre's FastAPI server
        const response = await fetch('http://localhost:8000/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payloadParaElBackend)
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            // extraction success
            step1.className = "step done";
            step1.innerHTML = `[Done] Repository cloned. ✅ ${data.file_count} files ready.`;
            
            step2.className = "step active";
            step2.innerHTML = "[Activate] Sending files to Antonio (AST Compression)...";

            // NOTE:
            // This is where you would take "data.files" and launch the POST to the Flask Blueprint
            // in endpoints.py so Antonio runs his AST script.
            console.log("Files ready for compression:", data.files);

            // Simulate the rest of the visual flow for the PoC
            setTimeout(() => {
                step2.className = "step done";
                step2.innerHTML = "[Done] Compressed Context JSON generated.";
                step3.className = "step active";
                step3.innerHTML = "[Activate] Uriel (Bob) analyzing and Gio formatting...";
            }, 2000);

            setTimeout(() => {
                step3.className = "step done";
                step3.innerHTML = "[Done] Documentation generated successfully.";
                btn.innerHTML = "Analysis Completed";
                btn.disabled = false; // Reactivate in case they want to analyze another
            }, 4500);

        } else {
            throw new Error(data.message || "Unknown error in extraction");
        }

    } catch (error) {
        console.error('Pipeline Error:', error);
        step1.className = "step waiting";
        step1.style.color = "#ff4444";
        step1.innerHTML = `[Error] Extraction failed: ${error.message}`;
        
        btn.innerHTML = "Retry";
        btn.disabled = false;
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
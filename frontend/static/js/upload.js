// Dynamic API Base resolution:
// If the frontend is served from Flask (port 5000), redirect API calls to the FastAPI backend (port 8000).
// Otherwise, keep them relative.
const API_BASE = window.location.port === '5000' ? 'http://localhost:8000' : '';

// select all button
document.addEventListener('DOMContentLoaded', () => {
    const selectAllBtn = document.getElementById('select-all-btn');
    let allSelected = false;

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            allSelected = !allSelected;
            const checkboxes = document.querySelectorAll('input[name="filters"]');
            
            checkboxes.forEach(cb => {
                cb.checked = allSelected;
            });

            selectAllBtn.innerHTML = allSelected
                ? 'Deselect All <span class="check-icon">✖</span>'
                : 'Select All <span class="check-icon">✔</span>';
            
            // Update download button visibility
            updateDownloadButtonVisibility();
        });
    }

    // Handle full documentation checkbox
    const fullDocCheckbox = document.getElementById('full-doc-checkbox');
    const downloadSection = document.getElementById('download-section');
    
    if (fullDocCheckbox && downloadSection) {
        fullDocCheckbox.addEventListener('change', () => {
            updateDownloadButtonVisibility();
        });
    }

    // Handle download button
    const downloadBtn = document.getElementById('download-docs-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownloadDocumentation);
    }
});

// Function to show/hide the download button
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

// Function to handle documentation download
async function handleDownloadDocumentation() {
    const btn = document.getElementById('download-docs-btn');
    let repoUrl = document.getElementById('repo-url').value;
    
    // Validate inputs
    if (!repoUrl) {
        alert('⚠️ Please enter a repository URL first');
        return;
    }
    
    // Clean URL if necessary
    let repository = repoUrl;
    if (repoUrl.includes('github.com')) {
        const urlParts = repoUrl.split('github.com/');
        if (urlParts.length > 1) {
            repository = urlParts[1].replace('.git', '');
        }
    }
    
    // Disable button and show loading state
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span style="margin-right: 8px;">⏳</span> Generating Documentation...';
    
    // Prepare payload with all filters enabled
    const payload = {
        repository: repository,
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
        const response = await fetch(`${API_BASE}/download-docs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            // Get the blob from the response
            const blob = await response.blob();
            
            // Extract filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'ODST_Technical_Documentation.md';
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/"/g, '');
                }
            }
            
            // Create temporary URL and download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('✅ Documentation downloaded successfully:', filename);
            
            // Show success message
            btn.innerHTML = '<span style="margin-right: 8px;">✅</span> Downloaded Successfully!';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }, 3000);
            
        } else {
            // Handle error
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
    const selectedFilters = {
        "overview": false,
        "architecture": false,
        "business-logic": false,
        "onboarding-path": false,
        "security-audit": false,
        "technical-debt": false
    };

    const checkboxes = document.querySelectorAll('input[name="filters"]');
    checkboxes.forEach((cb) => {
        if (selectedFilters.hasOwnProperty(cb.value)) {
            selectedFilters[cb.value] = cb.checked;
        }
    });

    // Collect input data
    let repoUrl = document.getElementById('repo-url').value;
    let repository = repoUrl;

    // Clean URL if user pasted the full GitHub link
    if (repoUrl.includes('github.com')) {
        const urlParts = repoUrl.split('github.com/');
        if (urlParts.length > 1) {
            repository = urlParts[1].replace('.git', '');
        }
    }

    // Prepare final payload for the backend
    const payload = {
        repository: repository,
        filters: selectedFilters, 
        extensions: null
    };

    console.log("JSON Payload to send:", payload);

    try {
        console.log("🚀 Sending request to backend...");
        console.log("Payload:", payload);
        
        // Call to FastAPI backend server
        const response = await fetch(`${API_BASE}/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
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
                // Filter only the modules that were selected
                const filteredPages = data.frontend_docs.pages.filter(page => selectedFilters[page.slug]);
                renderDynamicResults(filteredPages);
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
            errorDisplay = errorDisplay.substring(0, 200) + "... (see console for full details)";
        }
        
        step1.innerHTML = `[Error] ${errorDisplay}`;
        
        // Show additional error info in step 2
        step2.className = "step waiting";
        step2.style.color = "#ff8844";
        step2.innerHTML = "[Info] Check the browser console (F12) for more details";
        
        // Show troubleshooting tips in step 3
        step3.className = "step waiting";
        step3.style.color = "#ffaa44";
        step3.innerHTML = "[Tip] Verify: repository exists, correct permissions, server is running";
        
        btn.innerHTML = "Retry";
        btn.disabled = false;
        
        // Log helpful debugging info
        console.log("\n🔍 DEBUGGING INFORMATION:");
        console.log("Repository:", repository);
        console.log("Filters:", selectedFilters);
        console.log("\n💡 TROUBLESHOOTING TIPS:");
        console.log("1. Check that the repository exists and is accessible");
        console.log("2. Ensure the backend server is running");
        console.log("3. Check the backend console for detailed error logs");
    }
});
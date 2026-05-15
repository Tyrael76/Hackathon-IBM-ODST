document.getElementById('odst-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    // Ocultar boton y mostrar consola
    const btn = document.getElementById('analyze-btn');
    const consoleDiv = document.getElementById('status-console');
    
    btn.disabled = true;
    btn.innerHTML = "Procesando...";
    consoleDiv.style.display = "block";

    // Resetear estados visuales
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    
    step1.className = "step active"; step1.innerHTML = "[Active] Conectando con API de Extracción...";
    step2.className = "step waiting"; step2.innerHTML = "[Waiting] Esperando archivos...";
    step3.className = "step waiting"; step3.innerHTML = "[Waiting] Flujo de agentes...";

    // Recopilar datos 
    const token = document.getElementById('github-token').value;
    let repoUrl = document.getElementById('repo-url').value;
    
    // Limpiar URL si se pego el link completo
    let repository = repoUrl;
    if (repoUrl.includes('github.com')) {
        const urlParts = repoUrl.split('github.com/');
        if (urlParts.length > 1) {
            repository = urlParts[1].replace('.git', '');
        }
    }

    // Preparar Payload
    const payload = {
        github_token: token,
        repository: repository,
        extensions: null // Filtrado inteligente activado por defecto
    };

    try {
        // Llamada al backend
        const response = await fetch('http://localhost:8000/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            // Bien - Exito
            step1.className = "step done";
            step1.innerHTML = `[Done] Repositorio clonado. ${data.file_count} archivos extraídos.`;
            
            step2.className = "step active";
            step2.innerHTML = "[Activate] Enviando archivos a Antonio (Compresión AST)...";

            // NOTA: 
            // Aqui es donde se tomaria el "data.files" y se haria el siguiente fetch 
            // hacia el endpoint de Antonio/Flask para continuar el pipeline.
            console.log("Archivos listos para compresión:", data.files);

            // Simulamos el resto del flujo
            setTimeout(() => {
                step2.className = "step done";
                step2.innerHTML = "[Done] JSON comprimido generado.";
                step3.className = "step active";
                step3.innerHTML = "[Activate] Uriel/Bob analizando y Gio formateando...";
            }, 2000);

            setTimeout(() => {
                step3.className = "step done";
                step3.innerHTML = "[Done] Documentación generada con éxito.";
                btn.innerHTML = "Análisis Completado";
                btn.disabled = false; // Reactivamos por si quieren probar otro
            }, 4500);

        } else {
            // Manejo de errores de la API (ej. 400/500)
            throw new Error(data.message || "Error desconocido en la extracción");
        }

    } catch (error) {
        // Falló la conexión o el token es inválido
        console.error('Error de conexión:', error);
        step1.className = "step waiting";
        step1.style.color = "#ff4444"; // Rojo de error
        step1.innerHTML = `[Error] Fallo la extracción: ${error.message}`;
        
        btn.innerHTML = "Reintentar";
        btn.disabled = false;
    }
});
# 🎨 Guía para Rafiki - Frontend: Consumir API de Extracción

**Tu rol:** Crear la interfaz de usuario que permita a los usuarios ingresar un repositorio GitHub y visualizar los resultados del análisis.

---

## 🌐 API REST de Andre (Paso 2)

### Endpoint Base
```
http://localhost:8000
```

### Verificar que el servidor esté activo

**GET** `/`

```bash
curl http://localhost:8000/
```

**Respuesta:**
```json
{
  "message": "Servidor de Extracción Activo"
}
```

---

## 📡 Endpoint Principal: Extraer Repositorio

**POST** `/extract`

### Request Body (JSON):

```json
{
  "github_token": "ghp_xxxxxxxxxxxxx",
  "repository": "usuario/repositorio",
  "extensions": null
}
```

### Parámetros:

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `github_token` | string | ✅ Sí | Token de GitHub del usuario |
| `repository` | string | ✅ Sí | Formato: `usuario/repositorio` |
| `extensions` | array/null | ❌ No | `null` = filtrado inteligente, `[".py", ".js"]` = específico |

### Respuesta Exitosa (200):

```json
{
  "status": "success",
  "repo": "usuario/repositorio",
  "file_count": 42,
  "files": [
    {
      "path": "src/main.py",
      "content": "import os\nimport json\n...",
      "size": 1024,
      "dependencies": ["os", "json", "requests"]
    },
    {
      "path": "README.md",
      "content": "# Mi Proyecto\n...",
      "size": 512,
      "dependencies": []
    }
  ]
}
```

### Respuesta de Error (400/500):

```json
{
  "status": "error",
  "message": "Descripción del error"
}
```

---

## 💻 Ejemplos de Integración Frontend

### Ejemplo 1: JavaScript Vanilla (Fetch API)

```javascript
async function extraerRepositorio() {
    const token = document.getElementById('github-token').value;
    const repo = document.getElementById('repository').value;
    
    // Mostrar loading
    document.getElementById('loading').style.display = 'block';
    
    try {
        const response = await fetch('http://localhost:8000/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                github_token: token,
                repository: repo,
                extensions: null  // Filtrado inteligente
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log(`✅ ${data.file_count} archivos extraídos`);
            mostrarResultados(data.files);
        } else {
            console.error(`❌ Error: ${data.message}`);
            mostrarError(data.message);
        }
        
    } catch (error) {
        console.error('Error de conexión:', error);
        mostrarError('No se pudo conectar con el servidor');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function mostrarResultados(files) {
    const container = document.getElementById('resultados');
    container.innerHTML = '';
    
    files.forEach(file => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'file-item';
        fileDiv.innerHTML = `
            <h3>${file.path}</h3>
            <p>Tamaño: ${file.size} bytes</p>
            <p>Dependencias: ${file.dependencies.join(', ')}</p>
            <pre><code>${file.content.substring(0, 200)}...</code></pre>
        `;
        container.appendChild(fileDiv);
    });
}
```

### Ejemplo 2: React

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function RepositoryExtractor() {
    const [token, setToken] = useState('');
    const [repo, setRepo] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const handleExtract = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post('http://localhost:8000/extract', {
                github_token: token,
                repository: repo,
                extensions: null
            });

            if (response.data.status === 'success') {
                setResults(response.data);
            } else {
                setError(response.data.message);
            }
        } catch (err) {
            setError('Error de conexión con el servidor');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="extractor-container">
            <h1>Extractor de Repositorios GitHub</h1>
            
            <form onSubmit={handleExtract}>
                <input
                    type="text"
                    placeholder="Token de GitHub"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    required
                />
                
                <input
                    type="text"
                    placeholder="usuario/repositorio"
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                    required
                />
                
                <button type="submit" disabled={loading}>
                    {loading ? 'Extrayendo...' : 'Extraer Repositorio'}
                </button>
            </form>

            {error && (
                <div className="error">
                    ❌ Error: {error}
                </div>
            )}

            {results && (
                <div className="results">
                    <h2>✅ {results.file_count} archivos extraídos</h2>
                    <div className="files-list">
                        {results.files.map((file, index) => (
                            <div key={index} className="file-card">
                                <h3>{file.path}</h3>
                                <p>Tamaño: {file.size} bytes</p>
                                <p>Dependencias: {file.dependencies.join(', ')}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default RepositoryExtractor;
```

### Ejemplo 3: Vue.js

```vue
<template>
  <div class="extractor">
    <h1>Extractor de Repositorios GitHub</h1>
    
    <form @submit.prevent="extractRepo">
      <input
        v-model="token"
        type="text"
        placeholder="Token de GitHub"
        required
      />
      
      <input
        v-model="repository"
        type="text"
        placeholder="usuario/repositorio"
        required
      />
      
      <button type="submit" :disabled="loading">
        {{ loading ? 'Extrayendo...' : 'Extraer' }}
      </button>
    </form>

    <div v-if="error" class="error">
      ❌ {{ error }}
    </div>

    <div v-if="results" class="results">
      <h2>✅ {{ results.file_count }} archivos extraídos</h2>
      <div v-for="(file, index) in results.files" :key="index" class="file-card">
        <h3>{{ file.path }}</h3>
        <p>Tamaño: {{ file.size }} bytes</p>
        <p>Dependencias: {{ file.dependencies.join(', ') }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      token: '',
      repository: '',
      loading: false,
      results: null,
      error: null
    }
  },
  methods: {
    async extractRepo() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await fetch('http://localhost:8000/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            github_token: this.token,
            repository: this.repository,
            extensions: null
          })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
          this.results = data;
        } else {
          this.error = data.message;
        }
      } catch (err) {
        this.error = 'Error de conexión';
        console.error(err);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
```

---

## 🎨 Componentes UI Recomendados

### 1. Formulario de Entrada
```html
<form id="extract-form">
    <label>Token de GitHub:</label>
    <input type="password" id="github-token" required />
    
    <label>Repositorio (usuario/repo):</label>
    <input type="text" id="repository" placeholder="Ok-Andre/Pagina-web" required />
    
    <label>Filtrado:</label>
    <select id="filter-type">
        <option value="intelligent">Inteligente (Recomendado)</option>
        <option value="custom">Personalizado</option>
    </select>
    
    <button type="submit">Extraer Repositorio</button>
</form>
```

### 2. Indicador de Carga
```html
<div id="loading" style="display: none;">
    <div class="spinner"></div>
    <p>Extrayendo archivos del repositorio...</p>
</div>
```

### 3. Visualización de Resultados
```html
<div id="results">
    <h2>Archivos Extraídos: <span id="file-count">0</span></h2>
    
    <div id="files-container">
        <!-- Archivos se insertan aquí dinámicamente -->
    </div>
</div>
```

---

## 🔒 Seguridad

### ⚠️ IMPORTANTE: Manejo del Token

**NUNCA** guardes el token en:
- ❌ LocalStorage
- ❌ SessionStorage
- ❌ Cookies sin encriptar
- ❌ Variables globales

**Recomendaciones:**
- ✅ Pedir el token cada vez que el usuario lo necesite
- ✅ Usar HTTPS en producción
- ✅ Implementar autenticación en el backend
- ✅ Considerar OAuth para GitHub

---

## 🌐 CORS

El servidor de Andre ya tiene CORS configurado para desarrollo:
```python
allow_origins=["*"]  # Permite todas las origins
```

En **producción**, Andre debe cambiar esto a:
```python
allow_origins=["https://tu-dominio.com"]
```

---

## 📊 Flujo Completo del Pipeline

```
Usuario (Frontend/Rafiki)
    ↓
1. Ingresa repo + token
    ↓
2. POST /extract → Andre (Extracción)
    ↓
3. Archivos → Antonio (Compresión AST)
    ↓
4. AST → Uriel (Análisis IBM Bob)
    ↓
5. Análisis → Gio (Formato Markdown)
    ↓
6. Markdown → Rafiki (Mostrar al usuario)
```

---

## 🧪 Testing

### Probar con curl:
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "github_token": "tu_token",
    "repository": "Ok-Andre/Pagina-web",
    "extensions": null
  }'
```

### Probar con Postman:
1. Método: POST
2. URL: `http://localhost:8000/extract`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "github_token": "tu_token",
  "repository": "usuario/repo",
  "extensions": null
}
```

---

## 🆘 Troubleshooting

### Error: CORS Policy
**Problema:** `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solución:** Verifica que Andre tenga CORS habilitado en `main.py`

### Error: Connection Refused
**Problema:** `Failed to fetch` o `ERR_CONNECTION_REFUSED`

**Solución:** Verifica que el servidor de Andre esté corriendo:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Error: 401 Unauthorized
**Problema:** Token de GitHub inválido

**Solución:** Verifica que el token tenga permisos de lectura de repositorios

---

## 📞 Contacto

Si tienes dudas sobre la API, contacta a **Andre** (Paso 2 - Extracción)

Para el flujo completo del pipeline, coordina con todo el equipo.
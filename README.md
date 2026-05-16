# GitHub Repository Extractor - API REST + Custom Tool

Sistema de extracción de repositorios GitHub con **dos opciones de uso**:

1. **API REST** (HTTP) - Para integración con frontend
2. **Custom Tool** (Python) - Para uso directo en backend/agentes

## ✨ Características Principales

- 🔐 Autenticación con token de GitHub
- 🧠 **Filtrado inteligente por MIME type** (sin especificar extensiones)
- 📁 Filtrado tradicional por extensiones (opcional)
- 💾 Sistema de caché para optimizar llamadas
- 🌐 CORS configurado para frontend
- 📊 Extracción de dependencias de código

## 📋 Requisitos

- Python 3.9 o superior
- Token de GitHub

## 🚀 Instalación y Uso

### 1. Activar el entorno virtual

```bash
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar el servidor FastAPI

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: **http://localhost:8000**

### 4. Documentación interactiva

Una vez iniciado el servidor, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 Endpoints de la API

### `GET /`

Verifica que el servidor esté activo.

**Respuesta:**

```json
{
  "message": "Servidor de Extracción Activo"
}
```

### `POST /extract`

Extrae archivos de un repositorio de GitHub.

**Body (JSON):**

```json
{
  "github_token": "tu_token_aqui",
  "repository": "usuario/repositorio",
  "extensions": [".py", ".js", ".html"]
}
```

**Respuesta exitosa:**

```json
{
  "status": "success",
  "repo": "usuario/repositorio",
  "file_count": 15,
  "files": [
    {
      "path": "src/main.py",
      "dependencies": ["os", "json"],
      "content": "...",
      "size": 1024
    }
  ]
}
```

## 🔧 Opción 1: API REST (HTTP)

Ideal para **frontend** o **servicios externos**.

### Iniciar el servidor:

```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Hacer petición:

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "github_token": "tu_token",
    "repository": "usuario/repositorio",
    "extensions": null
  }'
```

**Documentación interactiva:** http://localhost:8000/docs

---

## 🐍 Opción 2: Custom Tool (Python)

Ideal para **backend**, **scripts** o **agentes de IA**.

### Uso Básico:

```python
from fetch_github_repo_tool import fetch_github_repo_tool

# Extracción con extensiones específicas
result = fetch_github_repo_tool(
    repository="usuario/repositorio",
    github_token="ghp_xxxxx",
    extensions=[".py", ".js", ".html"]
)

print(f"Archivos extraídos: {result['file_count']}")
```

### Con Filtrado Inteligente (Recomendado):

```python
from fetch_github_repo_tool import fetch_github_repo_tool

# El sistema detecta automáticamente archivos de texto usando MIME types
result = fetch_github_repo_tool(
    repository="usuario/repositorio",
    github_token="ghp_xxxxx",
    extensions=None  # Filtrado inteligente activado
)

# Descarta automáticamente:
# - Binarios (.exe, .dll, .so)
# - Imágenes (.png, .jpg, .gif)
# - Compilados (.pyc, .class)
# - Archivos comprimidos (.zip, .tar, .gz)
```

---

## 📁 Estructura del Proyecto

```
hIBM/
├── main.py                      # API REST FastAPI
├── gitAPI.py                    # Motor de extracción + filtrado MIME
├── fetch_github_repo_tool.py    # Custom Tool para uso directo
├── requirements.txt             # Dependencias
├── .env                         # Token GitHub (no compartir)
└── .gitignore                   # Archivos excluidos
```

## ⚙️ Configuración del Filtrado

### Filtrado Tradicional (Por Extensión)

```python
extensions = [".py", ".js", ".html", ".css"]
```

### Filtrado Inteligente (Por MIME Type)

El sistema detecta automáticamente:

**✅ Archivos Permitidos:**

- Texto plano (`text/*`)
- JSON (`application/json`)
- XML (`application/xml`)
- JavaScript (`application/javascript`)
- Python (`application/x-python`)
- YAML (`application/yaml`)
- Scripts shell (`application/x-sh`)

**❌ Archivos Rechazados:**

- Imágenes (`image/*`)
- Videos (`video/*`)
- Audio (`audio/*`)
- Binarios (`application/octet-stream`)
- Ejecutables (`application/x-executable`)
- PDFs (`application/pdf`)
- Archivos comprimidos (`application/zip`, `application/gzip`)

### Configuración Adicional

- **Tamaño máximo**: 150KB por archivo
- **Directorios excluidos**: `node_modules`, `__pycache__`, `.git`, `.venv`, `venv`, `env`, `.idea`, `.vscode`

---

## ⚙️ Configuración

### Filtrado Inteligente (MIME Type)

Detecta automáticamente el tipo de archivo:

**✅ Acepta:**

- Código: `.py`, `.js`, `.java`, `.kt`, `.go`, etc.
- Configuración: `.json`, `.yaml`, `.xml`, `.toml`
- Documentación: `.md`, `.txt`, `.rst`

**❌ Rechaza:**

- Binarios: `.exe`, `.dll`, `.so`
- Imágenes: `.png`, `.jpg`, `.gif`
- Compilados: `.pyc`, `.class`, `.jar`
- Comprimidos: `.zip`, `.tar`, `.gz`

### Límites

- **Tamaño máximo:** 150KB por archivo
- **Directorios excluidos:** `node_modules`, `__pycache__`, `.git`, `venv`

---

## 📝 Notas

- Token de GitHub es **sensible** - nunca lo compartas
- Sistema de caché evita límites de API
- CORS configurado para desarrollo (cambiar en producción)
- Entorno virtual (`venv/`) excluido de Git

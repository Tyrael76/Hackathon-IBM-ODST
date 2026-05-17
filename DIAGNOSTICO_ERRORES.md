# 🔍 Diagnóstico y Mejoras de Errores - Sistema ODST

## 📋 Problema Original

El sistema mostraba un error genérico: **"[Error] Extraction failed: Unknown error in extraction"**

Este mensaje no proporcionaba información suficiente para identificar la causa raíz del problema.

---

## ✅ Mejoras Implementadas

### 1. **Logging Detallado en `gitAPI.py`**

#### Antes:
```python
print(f"❌ CRITICAL CORE ERROR: {e}")
```

#### Después:
- ✅ Validación de autenticación con GitHub
- ✅ Verificación de acceso al repositorio
- ✅ Contador de archivos procesados/omitidos
- ✅ Progreso en tiempo real cada 10 directorios y 50 archivos
- ✅ Resumen detallado al finalizar
- ✅ Información del tipo de error y traceback completo

**Ejemplo de salida mejorada:**
```
🔍 [GITAPI] Starting extraction for: owner/repo
🔑 [GITAPI] Authenticating with GitHub...
✅ [GITAPI] Authenticated as: username
☁️ [GITAPI] Downloading owner/repo from GitHub...
✅ [GITAPI] Repository found: owner/repo
   📊 Stars: 123 | Forks: 45
📂 [GITAPI] Fetching repository contents...
✅ [GITAPI] Root contents fetched: 15 items
📁 [GITAPI] Processed 10 directories, 45 files so far...
✅ [GITAPI] Processed 50 files...

📊 [GITAPI] Extraction Summary:
   ✅ Files processed: 87
   ⏭️ Files skipped: 23
   📁 Directories scanned: 15
```

---

### 2. **Validación Mejorada en `fetch_github_repo_tool.py`**

#### Nuevas validaciones:
- ✅ Formato del token (mínimo 10 caracteres)
- ✅ Formato del repositorio (debe contener '/')
- ✅ Tipos de error específicos (`INVALID_TOKEN`, `INVALID_REPO_FORMAT`, `NO_FILES_FOUND`)
- ✅ Traceback completo en caso de excepciones

**Ejemplo de error específico:**
```json
{
  "status": "error",
  "message": "Invalid repository format. Expected 'owner/repo', got 'myrepo'",
  "error_type": "INVALID_REPO_FORMAT"
}
```

---

### 3. **Manejo de Errores Robusto en `main.py`**

#### Mejoras implementadas:
- ✅ Validación de inputs antes de procesamiento
- ✅ Verificación de existencia del archivo AST
- ✅ Manejo de errores JSON
- ✅ Captura de errores de CrewAI
- ✅ Respuestas de error estructuradas con traceback

**Ejemplo de respuesta de error:**
```json
{
  "error_type": "FileNotFoundError",
  "error_message": "AST generation failed - output file not created",
  "traceback": "Full Python traceback here..."
}
```

---

### 4. **Frontend Mejorado (`upload.js`)**

#### Antes:
```javascript
throw new Error(data.message || "Unknown error in extraction");
```

#### Después:
- ✅ Logging detallado en consola del navegador
- ✅ Parseo inteligente de errores JSON
- ✅ Mensajes de error truncados para UI (primeros 200 caracteres)
- ✅ Información adicional en los pasos 2 y 3
- ✅ Tips de troubleshooting automáticos
- ✅ Información de debugging en consola

**Ejemplo de salida en consola:**
```
🚀 Sending request to backend...
📡 Response status: 500
❌ Error details: {...}

🔍 DEBUGGING INFORMATION:
Repository: owner/repo
Token length: 40
Token starts with: ghp_...
Filters: {...}

💡 TROUBLESHOOTING TIPS:
1. Verify your GitHub token is valid and has repo access
2. Check that the repository exists and is accessible
3. Ensure the backend server is running on http://localhost:8000
4. Check the backend console for detailed error logs
```

---

## 🎯 Puntos de Diagnóstico Añadidos

### Nivel 1: Autenticación
- ✅ Validación de formato de token
- ✅ Test de autenticación con GitHub API
- ✅ Identificación del usuario autenticado

### Nivel 2: Acceso al Repositorio
- ✅ Verificación de existencia del repositorio
- ✅ Información de estrellas y forks
- ✅ Permisos de acceso

### Nivel 3: Extracción de Archivos
- ✅ Contador de archivos procesados
- ✅ Contador de archivos omitidos
- ✅ Razones de omisión (binarios, tamaño, blacklist)
- ✅ Progreso en tiempo real

### Nivel 4: Procesamiento
- ✅ Validación de AST generado
- ✅ Verificación de archivo de salida
- ✅ Errores de parseo JSON
- ✅ Errores de CrewAI

### Nivel 5: Frontend
- ✅ Logs detallados en consola del navegador
- ✅ Mensajes de error específicos en UI
- ✅ Tips de troubleshooting
- ✅ Información de debugging

---

## 🔧 Cómo Usar el Nuevo Sistema de Diagnóstico

### 1. **Ejecutar el Backend**
```bash
python main.py
```

### 2. **Abrir la Consola del Navegador (F12)**
- Pestaña "Console" para ver logs detallados
- Pestaña "Network" para ver requests/responses

### 3. **Intentar la Extracción**
- El sistema ahora mostrará exactamente dónde falla

### 4. **Revisar los Logs**

#### En el Backend (Terminal):
```
🔍 [GITAPI] Starting extraction for: owner/repo
🔑 [GITAPI] Authenticating with GitHub...
❌ [GITAPI] Authentication failed: Bad credentials
```

#### En el Frontend (Consola del Navegador):
```
❌ Pipeline Error: Error al extraer repositorio: Bad credentials
🔍 DEBUGGING INFORMATION:
Token length: 15
💡 TROUBLESHOOTING TIPS:
1. Verify your GitHub token is valid...
```

---

## 🐛 Errores Comunes y Soluciones

### Error: "Authentication failed: Bad credentials"
**Causa:** Token de GitHub inválido o expirado
**Solución:** 
1. Genera un nuevo token en GitHub Settings > Developer Settings > Personal Access Tokens
2. Asegúrate de que tenga permisos de `repo`

### Error: "Cannot access repository 'owner/repo'"
**Causa:** Repositorio no existe o es privado sin permisos
**Solución:**
1. Verifica que el repositorio existe
2. Si es privado, asegúrate de que tu token tenga acceso

### Error: "No se encontraron archivos válidos"
**Causa:** Todos los archivos son binarios o el filtro es muy restrictivo
**Solución:**
1. Revisa el resumen de extracción en los logs
2. Ajusta el filtro de extensiones si es necesario

### Error: "AST generation failed"
**Causa:** Error en el procesamiento de archivos Python
**Solución:**
1. Revisa los logs de `parser_core.py`
2. Verifica que los archivos Python tengan sintaxis válida

---

## 📊 Ejemplo de Flujo Completo con Logs

```
=== FRONTEND ===
🚀 Sending request to backend...
Payload: {repository: "owner/repo", github_token: "ghp_...", ...}

=== BACKEND (main.py) ===
🌐 [MAIN API] New extraction request received
   Repository: owner/repo
⚡ [MAIN API] Starting pipeline orchestration

=== PARSER CORE ===
🔄 [PIPELINE] Starting orchestration for: 'owner/repo'

=== GITAPI ===
🔍 [GITAPI] Starting extraction for: owner/repo
🔑 [GITAPI] Authenticating with GitHub...
✅ [GITAPI] Authenticated as: username
☁️ [GITAPI] Downloading owner/repo from GitHub...
✅ [GITAPI] Repository found: owner/repo
📊 [GITAPI] Extraction Summary:
   ✅ Files processed: 87

=== PARSER CORE ===
⚡ [COMPRESSION] Extracting cognitive structures in parallel...
   📊 Progress: 100/87 files processed
💾 [EXPORT] Saving consolidated results...
✅ CORE PIPELINE PROCESSED SUCCESSFULLY

=== BACKEND (main.py) ===
✅ [MAIN API] AST file generated, loading...
🤖 [MAIN API] Running CrewAI analysis
✅ [MAIN API] EXTRACTION COMPLETE

=== FRONTEND ===
✅ Extraction successful!
[Done] Repository cloned and processed.
[Done] Compressed Context JSON generated.
[Done] Documentation generated successfully.
```

---

## 🎉 Beneficios de las Mejoras

1. **Diagnóstico Preciso**: Identifica exactamente dónde y por qué falla el sistema
2. **Debugging Rápido**: Logs detallados en cada capa del sistema
3. **Experiencia de Usuario**: Mensajes de error claros y accionables
4. **Mantenibilidad**: Código más fácil de debuggear y mantener
5. **Troubleshooting**: Tips automáticos para resolver problemas comunes

---

## 📝 Notas Adicionales

- Todos los logs usan emojis para fácil identificación visual
- Los errores incluyen el tipo de excepción y traceback completo
- El sistema ahora valida inputs antes de procesarlos
- Los mensajes de error son específicos y accionables
- La consola del navegador muestra información de debugging detallada

---

**Última actualización:** 2026-05-17
**Autor:** Bob (Advanced Mode)
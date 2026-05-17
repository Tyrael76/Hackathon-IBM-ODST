# 🚀 Guía Oficial de Despliegue a Producción

**Hackathon IBM - ODST Team**  
**Stack:** FastAPI + Vanilla JS + IBM watsonx Orchestrate  
**Arquitectura:** OAuth 2.0 + Background Tasks + In-Memory Cache

---

## 📋 Tabla de Contenidos

1. [Preparación de Credenciales](#1-preparación-de-credenciales)
2. [Despliegue del Backend](#2-despliegue-del-backend)
3. [Despliegue del Frontend](#3-despliegue-del-frontend)
4. [Configuración del Agente watsonx](#4-configuración-del-agente-watsonx)
5. [Checklist de Pruebas Pre-Vuelo](#5-checklist-de-pruebas-pre-vuelo)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Preparación de Credenciales

### 1.1 GitHub OAuth Application

#### Paso 1: Acceder a GitHub Developer Settings
1. Ir a: https://github.com/settings/developers
2. Click en **"OAuth Apps"** → **"New OAuth App"**

#### Paso 2: Configurar la Aplicación OAuth

**Configuración para Producción:**

| Campo | Valor |
|-------|-------|
| **Application name** | `GitHub Extractor - Hackathon IBM` |
| **Homepage URL** | `https://tu-frontend.vercel.app` |
| **Authorization callback URL** | `https://tu-backend.onrender.com/auth/github/callback` |

⚠️ **CRÍTICO:** El `Authorization callback URL` debe coincidir EXACTAMENTE con tu URL de backend en producción + `/auth/github/callback`

#### Paso 3: Obtener Credenciales
Después de crear la app, obtendrás:
- **Client ID**: `Iv1.abc123def456` (público, se puede exponer)
- **Client Secret**: `ghp_xyz789...` (SECRETO, nunca exponerlo)

**Guardar estas credenciales de forma segura** - las necesitarás para configurar el backend.

---

### 1.2 IBM watsonx Assistant

#### Paso 1: Acceder a watsonx Assistant
1. Ir a: https://cloud.ibm.com/catalog/services/watson-assistant
2. Seleccionar tu instancia existente o crear una nueva

#### Paso 2: Obtener Credenciales del Web Chat

1. En el panel de watsonx Assistant, ir a **"Integrations"**
2. Seleccionar **"Web Chat"**
3. Click en **"Embed"** para ver las credenciales

Necesitarás:
- **Integration ID**: `abc123-def456-ghi789` (público)
- **Region**: `us-south` o `eu-gb` (público)

#### Paso 3: Configurar Variables de Sesión en el Agente

En el **Actions Editor** de watsonx:

1. Crear una nueva variable de sesión llamada: `codigo_extraido`
2. Tipo: `String` (JSON serializado)
3. Esta variable recibirá automáticamente el código extraído del repositorio

**Ejemplo de estructura que recibirá el agente:**
```json
{
  "repositorio": "facebook/react",
  "total_archivos": 42,
  "archivos": [
    {
      "ruta": "src/index.js",
      "extension": ".js",
      "tamaño_kb": "12.45",
      "contenido": "import React from 'react'..."
    }
  ]
}
```

---

## 2. Despliegue del Backend

### 2.1 Plataforma Recomendada: Render.com

**¿Por qué Render?**
- ✅ Soporte nativo para Python/FastAPI
- ✅ Variables de entorno seguras
- ✅ HTTPS automático
- ✅ Tier gratuito disponible
- ✅ Fácil integración con GitHub

#### Paso 1: Crear Nuevo Web Service

1. Ir a: https://dashboard.render.com/
2. Click en **"New +"** → **"Web Service"**
3. Conectar tu repositorio de GitHub

#### Paso 2: Configuración del Servicio

| Campo | Valor |
|-------|-------|
| **Name** | `github-extractor-backend` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |

⚠️ **CRÍTICO:** El flag `--workers 1` es OBLIGATORIO para proteger la `DemoCache` en memoria. Múltiples workers causarán inconsistencias de datos.

#### Paso 3: Variables de Entorno

En la sección **"Environment Variables"**, agregar:

```bash
# GitHub OAuth (OBLIGATORIO)
GITHUB_CLIENT_ID=Iv1.abc123def456
GITHUB_CLIENT_SECRET=ghp_xyz789abc123def456ghi789jkl012mno345pqr678

# IBM watsonx (OBLIGATORIO)
WATSONX_INTEGRATION_ID=abc123-def456-ghi789
WATSONX_REGION=us-south

# URLs de Aplicación (OBLIGATORIO)
BACKEND_URL=https://github-extractor-backend.onrender.com
FRONTEND_URL=https://tu-frontend.vercel.app

# Seguridad (OBLIGATORIO)
SESSION_SECRET_KEY=genera_un_token_aleatorio_de_minimo_32_caracteres_aqui
ENVIRONMENT=production
```

**Generar SESSION_SECRET_KEY seguro:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Paso 4: Deploy

1. Click en **"Create Web Service"**
2. Render automáticamente:
   - Clonará tu repositorio
   - Instalará dependencias
   - Iniciará el servidor
   - Asignará una URL pública

**Tu backend estará disponible en:** `https://github-extractor-backend.onrender.com`

---

### 2.2 Alternativa: Railway.app

Si prefieres Railway:

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Inicializar proyecto
railway init

# Configurar variables de entorno
railway variables set GITHUB_CLIENT_ID=Iv1.abc123def456
railway variables set GITHUB_CLIENT_SECRET=ghp_xyz789...
railway variables set WATSONX_INTEGRATION_ID=abc123-def456
railway variables set WATSONX_REGION=us-south
railway variables set BACKEND_URL=https://tu-proyecto.up.railway.app
railway variables set FRONTEND_URL=https://tu-frontend.vercel.app
railway variables set SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set ENVIRONMENT=production

# Deploy
railway up
```

---

### 2.3 Verificación del Backend

**Prueba de Health Check:**
```bash
curl https://tu-backend.onrender.com/
```

**Respuesta esperada:**
```json
{
  "status": "active",
  "service": "GitHub OAuth Extractor",
  "version": "2.0.0"
}
```

**Prueba de OAuth Status:**
```bash
curl https://tu-backend.onrender.com/auth/status
```

**Respuesta esperada:**
```json
{
  "oauth_configured": true,
  "environment": "production"
}
```

---

## 3. Despliegue del Frontend

### 3.1 Plataforma Recomendada: Vercel

**¿Por qué Vercel?**
- ✅ Deploy instantáneo desde GitHub
- ✅ HTTPS automático
- ✅ CDN global
- ✅ Tier gratuito generoso
- ✅ Preview deployments automáticos

#### Paso 1: Preparar el Frontend

**Actualizar URLs en los archivos HTML:**

En `frontend/templetes/oauth_index.html` (línea 247):
```javascript
// ANTES (desarrollo)
const BACKEND_URL = 'http://localhost:8000';

// DESPUÉS (producción)
const BACKEND_URL = 'https://tu-backend.onrender.com';
```

En `frontend/templetes/procesando.html` (línea 225):
```javascript
// ANTES (desarrollo)
const BACKEND_URL = 'http://localhost:8000';

// DESPUÉS (producción)
const BACKEND_URL = 'https://tu-backend.onrender.com';
```

#### Paso 2: Estructura de Archivos para Vercel

Crear `vercel.json` en la raíz del proyecto:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/templetes/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/",
      "dest": "/frontend/templetes/oauth_index.html"
    },
    {
      "src": "/procesando",
      "dest": "/frontend/templetes/procesando.html"
    },
    {
      "src": "/results",
      "dest": "/frontend/templetes/results.html"
    }
  ]
}
```

#### Paso 3: Deploy a Vercel

**Opción A: Desde la Web UI**
1. Ir a: https://vercel.com/new
2. Importar tu repositorio de GitHub
3. Vercel detectará automáticamente la configuración
4. Click en **"Deploy"**

**Opción B: Desde CLI**
```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Tu frontend estará disponible en:** `https://tu-proyecto.vercel.app`

---

### 3.2 Alternativa: Netlify

Si prefieres Netlify:

1. Crear `netlify.toml` en la raíz:
```toml
[build]
  publish = "frontend/templetes"

[[redirects]]
  from = "/"
  to = "/oauth_index.html"
  status = 200

[[redirects]]
  from = "/procesando"
  to = "/procesando.html"
  status = 200

[[redirects]]
  from = "/results"
  to = "/results.html"
  status = 200
```

2. Deploy:
```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
netlify deploy --prod --dir=frontend/templetes
```

---

### 3.3 Alternativa: GitHub Pages

Para GitHub Pages (más simple pero menos flexible):

1. Crear rama `gh-pages`
2. Copiar archivos de `frontend/templetes/` a la raíz
3. Actualizar URLs del backend en los archivos
4. Push a la rama `gh-pages`
5. Habilitar GitHub Pages en Settings → Pages

---

### 3.4 Actualizar Callback URL en GitHub

**IMPORTANTE:** Después de desplegar el backend, actualizar la OAuth App:

1. Ir a: https://github.com/settings/developers
2. Seleccionar tu OAuth App
3. Actualizar **"Authorization callback URL"** a:
   ```
   https://tu-backend.onrender.com/auth/github/callback
   ```
4. Click en **"Update application"**

---

## 4. Configuración del Agente watsonx

### 4.1 Configurar Variable de Contexto

En el **Actions Editor** de watsonx Assistant:

#### Paso 1: Crear Variable de Sesión

1. Ir a **"Variables"** → **"Session variables"**
2. Click en **"New session variable"**
3. Configurar:
   - **Name:** `codigo_extraido`
   - **Type:** `String`
   - **Initial value:** (dejar vacío)

#### Paso 2: Usar la Variable en Actions

En tus Actions, puedes acceder al código extraído con:

```
${codigo_extraido}
```

**Ejemplo de Action:**
```
User says: "Analiza el código"

Assistant response:
He recibido el código del repositorio. Déjame analizarlo...

[Aquí el agente puede procesar ${codigo_extraido}]
```

#### Paso 3: Parsear el JSON (Opcional)

Si necesitas acceder a campos específicos, usa expresiones SpEL:

```
Total de archivos: ${codigo_extraido.total_archivos}
Repositorio: ${codigo_extraido.repositorio}
```

---

### 4.2 Configurar Integración Web Chat

En **"Integrations"** → **"Web Chat"**:

1. **Appearance:**
   - Personalizar colores y logo según tu branding
   - Configurar mensaje de bienvenida

2. **Security:**
   - Habilitar **"Secure your web chat"** si es necesario
   - Configurar dominios permitidos

3. **Advanced:**
   - Habilitar **"Session history"** para debugging
   - Configurar timeout de sesión

---

### 4.3 Verificar Inyección de Contexto

El frontend inyecta automáticamente el contexto en `procesando.html` (líneas 398-400):

```javascript
instance.updateSessionVariables({
    codigo_extraido: JSON.stringify(codigoExtraido, null, 2)
});
```

**Para verificar que funciona:**
1. Extraer un repositorio de prueba
2. Abrir el chat de watsonx
3. En la consola del navegador, verificar:
   ```javascript
   console.log('[WATSONX] Context injected:', codigoExtraido.total_archivos, 'files');
   ```

---

## 5. Checklist de Pruebas Pre-Vuelo

### ✅ Test 1: CORS y Conectividad

**Objetivo:** Verificar que el frontend puede comunicarse con el backend.

```bash
# Desde la consola del navegador en tu frontend
fetch('https://tu-backend.onrender.com/')
  .then(r => r.json())
  .then(console.log)
```

**Resultado esperado:**
```json
{
  "status": "active",
  "service": "GitHub OAuth Extractor",
  "version": "2.0.0"
}
```

**Si falla:**
- Verificar que `FRONTEND_URL` en el backend coincida con tu dominio de Vercel
- Revisar logs del backend para errores CORS
- Confirmar que el backend está corriendo

---

### ✅ Test 2: OAuth Flow Completo

**Objetivo:** Verificar que el flujo OAuth funciona end-to-end.

**Pasos:**
1. Ir a tu frontend: `https://tu-proyecto.vercel.app`
2. Ingresar un repositorio público: `octocat/Hello-World`
3. Click en **"Connect with GitHub"**
4. Autorizar la aplicación en GitHub
5. Esperar redirección a `/procesando`
6. Verificar que el polling funciona (spinner girando)
7. Esperar a que se complete la extracción
8. Verificar que aparece el mensaje de éxito

**Resultado esperado:**
- ✅ Redirección a GitHub exitosa
- ✅ Callback procesa correctamente
- ✅ Polling muestra progreso
- ✅ Extracción completa sin errores
- ✅ Chat de watsonx se carga automáticamente

**Si falla en la redirección:**
- Verificar que el `Authorization callback URL` en GitHub coincida con tu backend
- Revisar logs del backend para errores de token exchange

**Si falla el polling:**
- Abrir DevTools → Network → verificar llamadas a `/api/status/{repo}`
- Revisar logs del backend para errores en background tasks

---

### ✅ Test 3: Inyección de IA y Contexto

**Objetivo:** Verificar que el agente de watsonx recibe el código extraído.

**Pasos:**
1. Completar una extracción exitosa (Test 2)
2. Cuando se abra el chat de watsonx, escribir:
   ```
   ¿Cuántos archivos extrajiste?
   ```
3. El agente debe responder con el número correcto de archivos

**Resultado esperado:**
- ✅ Chat de watsonx se abre automáticamente
- ✅ Mensaje de bienvenida menciona el repositorio
- ✅ Agente tiene acceso a la variable `codigo_extraido`
- ✅ Agente puede responder preguntas sobre el código

**Si falla:**
- Abrir DevTools → Console → buscar logs `[WATSONX]`
- Verificar que `/api/chat-config` retorna credenciales correctas:
  ```bash
  curl https://tu-backend.onrender.com/api/chat-config
  ```
- Revisar que `WATSONX_INTEGRATION_ID` y `WATSONX_REGION` sean correctos
- Verificar en watsonx Assistant que la variable `codigo_extraido` existe

---

## 6. Troubleshooting

### Problema: "OAuth not configured"

**Síntoma:** Botón de GitHub deshabilitado con mensaje de error.

**Solución:**
1. Verificar que `GITHUB_CLIENT_ID` y `GITHUB_CLIENT_SECRET` estén configurados en el backend
2. Confirmar que no contengan valores placeholder (`your_...`)
3. Reiniciar el servicio del backend después de cambiar variables

---

### Problema: "State mismatch" o "CSRF attack"

**Síntoma:** Error 403 después de autorizar en GitHub.

**Solución:**
1. Verificar que las cookies estén habilitadas en el navegador
2. Confirmar que `BACKEND_URL` y `FRONTEND_URL` sean correctos
3. En producción, asegurar que `ENVIRONMENT=production` para habilitar cookies seguras
4. Verificar que el dominio del frontend coincida exactamente con `FRONTEND_URL`

---

### Problema: "Gateway Timeout" durante extracción

**Síntoma:** Error 504 o timeout después de autorizar.

**Solución:**
- ✅ **Ya está resuelto:** El código usa `BackgroundTasks` para evitar timeouts
- Si persiste, verificar logs del backend para errores en `orchestrate_pipeline`
- Confirmar que el repositorio sea accesible y no demasiado grande

---

### Problema: Chat de watsonx no se carga

**Síntoma:** No aparece el widget de chat después de la extracción.

**Solución:**
1. Abrir DevTools → Console → buscar errores de `[WATSONX]`
2. Verificar que `/api/chat-config` retorne datos válidos
3. Confirmar que `WATSONX_INTEGRATION_ID` sea correcto
4. Revisar que el script de watsonx se cargue:
   ```javascript
   // En DevTools Console
   console.log(window.watsonAssistantChatOptions);
   ```

---

### Problema: "No files found in repository"

**Síntoma:** Extracción completa pero sin archivos.

**Solución:**
1. Verificar que el repositorio sea público o que tengas acceso
2. Confirmar que el repositorio contenga archivos de código
3. Revisar los filtros de extensiones si se especificaron
4. Verificar logs del backend para errores en `gitAPI.get_repository_data`

---

### Problema: CORS errors en producción

**Síntoma:** Errores de CORS en la consola del navegador.

**Solución:**
1. Verificar que `FRONTEND_URL` en el backend coincida EXACTAMENTE con tu dominio de Vercel
2. Incluir el protocolo: `https://` (no `http://`)
3. No incluir trailing slash: `https://tu-proyecto.vercel.app` (no `.../`)
4. Reiniciar el backend después de cambiar `FRONTEND_URL`

---

## 📊 Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (Vercel/Netlify)                       │
│  • oauth_index.html (inicio OAuth)                           │
│  • procesando.html (polling + watsonx)                       │
│  • results.html (resultados)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS + CORS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            BACKEND (Render/Railway)                          │
│  FastAPI + Uvicorn (--workers 1)                             │
│                                                               │
│  Endpoints:                                                   │
│  • POST /auth/github/initiate                                │
│  • GET  /auth/github/callback                                │
│  • GET  /api/status/{repo}                                   │
│  • GET  /api/chat-config                                     │
│                                                               │
│  Componentes:                                                 │
│  • DemoCache (in-memory, thread-safe)                        │
│  • BackgroundTasks (async extraction)                        │
│  • OAuth 2.0 (stateless CSRF)                                │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────────┐
│  GitHub API      │          │  IBM watsonx         │
│  • OAuth         │          │  • Web Chat SDK      │
│  • Repository    │          │  • Orchestrate Agent │
│  • Code Access   │          │  • Context Variables │
└──────────────────┘          └──────────────────────┘
```

---

## 🔐 Seguridad en Producción

### Variables de Entorno Sensibles

**NUNCA exponer en el frontend:**
- ❌ `GITHUB_CLIENT_SECRET`
- ❌ `SESSION_SECRET_KEY`

**Seguro exponer (público):**
- ✅ `GITHUB_CLIENT_ID`
- ✅ `WATSONX_INTEGRATION_ID`
- ✅ `WATSONX_REGION`

### Tokens Efímeros

- Los tokens de GitHub **NUNCA** se almacenan
- Existen solo en memoria durante la ejecución de `orchestrate_pipeline`
- Se descartan automáticamente por garbage collection
- No se registran en logs

### HTTPS Obligatorio

- Render y Vercel proveen HTTPS automático
- Las cookies OAuth usan flag `Secure` en producción
- `SameSite=Lax` previene CSRF

---

## 📈 Monitoreo y Logs

### Backend (Render)

Acceder a logs en tiempo real:
```bash
# Desde Render Dashboard
Logs → View Logs

# Buscar errores
[ERROR] OAuth callback failed
[WARNING] State mismatch
[BACKGROUND] Extraction successful
```

### Frontend (Vercel)

Monitorear en Vercel Dashboard:
- **Analytics:** Tráfico y performance
- **Logs:** Errores de build y runtime
- **Deployments:** Historial de deploys

### watsonx Assistant

Revisar conversaciones:
1. Ir a **"Analytics"** en watsonx Assistant
2. Ver **"User conversations"**
3. Verificar que `codigo_extraido` se inyecta correctamente

---

## 🎯 Optimizaciones Post-Hackathon

Para escalar después del hackathon:

1. **Reemplazar DemoCache con Redis:**
   ```python
   # Usar Redis para cache distribuido
   import redis
   cache = redis.Redis(host='...', port=6379)
   ```

2. **Agregar Rate Limiting:**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

3. **Implementar Queue System:**
   ```python
   # Usar Celery para background tasks
   from celery import Celery
   app = Celery('tasks', broker='redis://...')
   ```

4. **Agregar Persistencia:**
   - Base de datos para resultados
   - S3 para archivos grandes
   - TTL para limpieza automática

---

## ✅ Checklist Final

Antes de la presentación del hackathon:

- [ ] Backend desplegado y accesible
- [ ] Frontend desplegado y accesible
- [ ] OAuth callback URL actualizado en GitHub
- [ ] Variables de entorno configuradas correctamente
- [ ] Test 1 (CORS) pasado ✅
- [ ] Test 2 (OAuth) pasado ✅
- [ ] Test 3 (IA) pasado ✅
- [ ] Chat de watsonx funcionando
- [ ] Logs del backend sin errores críticos
- [ ] Demo con repositorio de prueba exitosa

---

## 📞 Soporte

Si encuentras problemas durante el despliegue:

1. **Revisar logs del backend** (Render/Railway Dashboard)
2. **Abrir DevTools** en el navegador (Console + Network)
3. **Verificar variables de entorno** (typos comunes)
4. **Consultar la sección de Troubleshooting** arriba

---

**¡Buena suerte en el hackathon! 🚀**

*Documento generado por Bob - Lead DevOps Engineer*
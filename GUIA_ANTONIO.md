# 🔧 Guía para Antonio - Paso 3: Compresión con AST

**Tu rol:** Recibir archivos de código de Andre y comprimirlos usando AST/Regex antes de pasarlos a Uriel.

---

## 📥 Opción 1: Usar Custom Tool (Recomendado)

### Ventajas:
- ✅ Más rápido (sin HTTP)
- ✅ Más simple (importación directa)
- ✅ Mismo proceso de Python

### Paso 1: Importar la herramienta

```python
from fetch_github_repo_tool import fetch_github_repo_tool
```

### Paso 2: Llamar la función

```python
# Obtener archivos del repositorio
result = fetch_github_repo_tool(
    repository="usuario/repositorio",
    github_token="tu_token_github",
    extensions=None  # Filtrado inteligente automático
)

# Verificar éxito
if result['status'] == 'success':
    print(f"✅ {result['file_count']} archivos recibidos")
    files = result['files']
else:
    print(f"❌ Error: {result['message']}")
```

### Paso 3: Procesar cada archivo con AST

```python
import ast
import json

def comprimir_con_ast(codigo_fuente):
    """
    Tu función de compresión AST aquí
    """
    try:
        tree = ast.parse(codigo_fuente)
        # Tu lógica de compresión
        return {
            'compressed': True,
            'ast_data': ast.dump(tree),
            'size_original': len(codigo_fuente)
        }
    except:
        return {'compressed': False, 'error': 'No es Python válido'}

# Procesar todos los archivos
archivos_comprimidos = []

for file in result['files']:
    print(f"📄 Procesando: {file['path']}")
    
    # Comprimir con AST
    compressed = comprimir_con_ast(file['content'])
    
    archivos_comprimidos.append({
        'path': file['path'],
        'original_size': file['size'],
        'compressed_data': compressed,
        'dependencies': file['dependencies']
    })

# Guardar resultado para Uriel (Paso 4)
with open('archivos_comprimidos_para_uriel.json', 'w') as f:
    json.dump(archivos_comprimidos, f, indent=2)

print(f"✅ {len(archivos_comprimidos)} archivos comprimidos")
print("📤 Listos para Uriel en: archivos_comprimidos_para_uriel.json")
```

### Ejemplo Completo:

```python
# antonio_pipeline.py
from fetch_github_repo_tool import fetch_github_repo_tool
import ast
import json

def main():
    # 1. Recibir archivos de Andre
    print("📥 Paso 3: Recibiendo archivos de Andre...")
    
    result = fetch_github_repo_tool(
        repository="startuplab-mx/HCKMX26-1776352533",
        github_token="tu_token_aqui",
        extensions=None
    )
    
    if result['status'] != 'success':
        print(f"❌ Error: {result['message']}")
        return
    
    print(f"✅ {result['file_count']} archivos recibidos")
    
    # 2. Comprimir con AST
    print("🔄 Comprimiendo con AST...")
    
    archivos_comprimidos = []
    for file in result['files']:
        # Tu lógica de compresión aquí
        compressed = {
            'path': file['path'],
            'size_original': file['size'],
            'content_compressed': file['content'][:100] + '...',  # Ejemplo
            'dependencies': file['dependencies']
        }
        archivos_comprimidos.append(compressed)
    
    # 3. Guardar para Uriel
    with open('para_uriel.json', 'w') as f:
        json.dump(archivos_comprimidos, f, indent=2)
    
    print(f"✅ Compresión completa: {len(archivos_comprimidos)} archivos")
    print("📤 Archivo listo para Uriel: para_uriel.json")

if __name__ == "__main__":
    main()
```

---

## 🌐 Opción 2: Usar API REST (HTTP)

### Ventajas:
- ✅ Desacoplado de Andre
- ✅ Puede estar en otro servidor
- ✅ Fácil de escalar

### Paso 1: Verificar que el servidor esté corriendo

Andre debe tener el servidor activo:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Hacer petición HTTP

```python
import requests
import json

# Hacer petición a la API de Andre
response = requests.post(
    "http://localhost:8000/extract",
    json={
        "github_token": "tu_token_github",
        "repository": "usuario/repositorio",
        "extensions": None  # Filtrado inteligente
    }
)

# Verificar respuesta
if response.status_code == 200:
    result = response.json()
    print(f"✅ {result['file_count']} archivos recibidos")
    files = result['files']
else:
    print(f"❌ Error HTTP {response.status_code}")
```

### Paso 3: Procesar archivos (igual que Opción 1)

```python
# Comprimir cada archivo
archivos_comprimidos = []

for file in files:
    # Tu lógica de compresión AST
    compressed = comprimir_con_ast(file['content'])
    
    archivos_comprimidos.append({
        'path': file['path'],
        'compressed_data': compressed
    })

# Guardar para Uriel
with open('para_uriel.json', 'w') as f:
    json.dump(archivos_comprimidos, f, indent=2)
```

---

## 📊 Estructura de Datos que Recibes

Cada archivo tiene esta estructura:

```python
{
    'path': 'src/main.py',           # Ruta del archivo
    'content': 'import os\n...',     # Código completo en texto
    'size': 1024,                    # Tamaño en bytes
    'dependencies': ['os', 'json']   # Imports detectados
}
```

---

## 🎯 Tu Trabajo (Paso 3)

1. **Recibir** archivos de Andre (Paso 2)
2. **Comprimir** usando AST/Regex
3. **Pasar** a Uriel (Paso 4) para análisis con IBM Bob

---

## 💡 Recomendación

**Usa Opción 1 (Custom Tool)** porque:
- Es más rápido
- No depende de que Andre tenga el servidor corriendo
- Más fácil de debuggear
- Mismo entorno de Python

---

## 🆘 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'fetch_github_repo_tool'`
**Solución:** Asegúrate de estar en el mismo directorio que `fetch_github_repo_tool.py` o agrégalo al PYTHONPATH:
```python
import sys
sys.path.append('/ruta/al/proyecto/hIBM')
from fetch_github_repo_tool import fetch_github_repo_tool
```

### Error: `Connection refused` (Opción 2)
**Solución:** Verifica que Andre tenga el servidor corriendo en `http://localhost:8000`

### Error: Token inválido
**Solución:** Verifica que tu token de GitHub tenga permisos de lectura de repositorios

---

## 📞 Contacto

Si tienes dudas, contacta a **Andre** (Paso 2 - Extracción)
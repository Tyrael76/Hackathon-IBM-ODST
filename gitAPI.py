import os
import json
import re
import mimetypes
from github import Github

# Configuración de Filtros Estáticos
MAX_FILE_SIZE = 150 * 1024  # 150KB
BLACKLIST_DIRS = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', '.idea', '.vscode'}

# Inicializar mimetypes
mimetypes.init()

def is_text_file(path):
    """
    Filtrado Inteligente sin Tokens (Instrucción 3):
    Usa mimetypes para detectar si un archivo es texto plano.
    Lee los primeros bytes para descartar binarios, imágenes y compilados.
    """
    # Obtener el tipo MIME basado en la extensión
    mime_type, _ = mimetypes.guess_type(path)
    
    # Si no se puede determinar, asumir que es texto
    if mime_type is None:
        return True
    
    # Permitir tipos de texto explícitos
    if mime_type.startswith('text/'):
        return True
    
    # Permitir tipos específicos de código/configuración
    allowed_types = {
        'application/json',
        'application/xml',
        'application/javascript',
        'application/x-javascript',
        'application/x-python',
        'application/x-sh',
        'application/x-yaml',
        'application/yaml',
    }
    
    if mime_type in allowed_types:
        return True
    
    # Rechazar binarios, imágenes, compilados
    binary_types = {
        'image/', 'video/', 'audio/',
        'application/octet-stream',
        'application/x-executable',
        'application/x-sharedlib',
        'application/pdf',
        'application/zip',
        'application/x-tar',
        'application/gzip',
    }
    
    for binary_type in binary_types:
        if mime_type.startswith(binary_type):
            return False
    
    return True

def is_valid_file(path, allowed_exts):
    """
    Verifica si el archivo es válido según ruta y extensión.
    Si allowed_exts está vacío, usa filtrado inteligente por MIME type.
    """
    parts = path.split('/')
    if any(part in BLACKLIST_DIRS for part in parts):
        return False
    
    # Si se especificaron extensiones, usar filtrado tradicional
    if allowed_exts:
        return any(path.endswith(ext) for ext in allowed_exts)
    
    # Si no hay extensiones especificadas, usar filtrado inteligente
    return is_text_file(path)

def extract_dependencies(content):
    """Detecta imports básicos para ayudar al mapa de dependencias."""
    pattern = r"^(?:from|import)\s+([\w\.]+)"
    return list(set(re.findall(pattern, content, re.MULTILINE)))

def get_repository_data(repo_full_name, token, allowed_exts):
    """
    Motor principal de extracción. 
    Recibe los parámetros dinámicos desde el endpoint de FastAPI.
    """
    g = Github(token)
    cache_name = f"cache_{repo_full_name.replace('/', '_')}.json"
    
    if os.path.exists(cache_name):
        print(f"--- 💾 Cargando {repo_full_name} desde caché local ---")
        with open(cache_name, 'r', encoding='utf-8') as f:
            return json.load(f)

    print(f"--- ☁️ Descargando {repo_full_name} desde GitHub ---")
    try:
        repo = g.get_repo(repo_full_name)
        all_files = []
        contents = repo.get_contents("")

        while contents:
            file_item = contents.pop(0)
            
            if file_item.type == "dir":
                # Si la carpeta está en blacklist, no entramos
                if file_item.name in BLACKLIST_DIRS:
                    continue
                contents.extend(repo.get_contents(file_item.path))
                continue
                
            if is_valid_file(file_item.path, allowed_exts) and file_item.size <= MAX_FILE_SIZE:
                try:
                    raw_content = file_item.decoded_content.decode('utf-8')
                    all_files.append({
                        "path": file_item.path,
                        "dependencies": extract_dependencies(raw_content),
                        "content": raw_content,
                        "size": file_item.size
                    })
                    print(f"✅ Procesado: {file_item.path}")
                except Exception as e:
                    print(f"⚠️ Error en {file_item.path}: {e}")

        # Guardar caché y entrega
        with open(cache_name, 'w', encoding='utf-8') as f:
            json.dump(all_files, f, indent=4, ensure_ascii=False)
        
        return all_files

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN CORE: {e}")
        raise e # Re-lanzamos para que FastAPI capture el error
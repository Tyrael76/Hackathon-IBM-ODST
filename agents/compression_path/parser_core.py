import os # Necesario para sacar la extensión
from parser_py import compress_python_code
from parser_regex import compress_regex_code # ¡Tu nuevo analizador!

# ... (código previo) ...

    # PASO 2: Compresión Estructural (TU Lógica)
    for archivo in archivos_crudos:
        ruta = archivo['path']
        contenido = archivo['content']
        
        # Extraemos la extensión del archivo (ej. '.js', '.py')
        _, extension = os.path.splitext(ruta.lower())
        
        if extension == '.py':
            print(f"   ⚙️ Comprimiendo con AST: {ruta}")
            estructura_limpia = compress_python_code(contenido)
            
            if "error" not in estructura_limpia:
                repositorio_comprimido[ruta] = {
                    "tipo": "python",
                    "dependencias_externas": archivo.get('dependencies', []),
                    "estructura": estructura_limpia
                }
                
        # ¡LA CONEXIÓN DE LA NUEVA PIEZA!
        elif extension in ['.js', '.ts', '.jsx', '.tsx', '.kt', '.java', '.cs']:
            print(f"   🔍 Comprimiendo con Regex: {ruta}")
            estructura_limpia = compress_regex_code(contenido, extension)
            
            # Solo lo guardamos si la Regex logró extraer al menos una función o clase
            if estructura_limpia: 
                repositorio_comprimido[ruta] = {
                    "tipo": extension.replace('.', ''), # ej. "js" o "kt"
                    "dependencias_externas": archivo.get('dependencies', []),
                    "estructura": estructura_limpia
                }
        else:
            # Archivos de texto plano (.md, .txt) o desconocidos
            # Se los pasamos a Uriel tal cual, pero truncados para no gastar tokens
            repositorio_comprimido[ruta] = {
                "tipo": "texto_plano",
                "preview": contenido[:150] + "... [TRUNCADO]"
            }
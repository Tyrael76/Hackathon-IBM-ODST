"""
Ejemplo para Antonio - Paso 3: Compresión con AST
Demuestra cómo usar fetch_github_repo_tool para recibir archivos de Andre
y procesarlos con AST antes de pasarlos a Uriel.
"""

from fetch_github_repo_tool import fetch_github_repo_tool
import json
import ast

def comprimir_con_ast(codigo_fuente, path):
    """
    Función de ejemplo para comprimir código usando AST.
    Antonio debe reemplazar esto con su lógica real de compresión.
    """
    try:
        # Intentar parsear como Python
        if path.endswith('.py'):
            tree = ast.parse(codigo_fuente)
            
            # Ejemplo: Extraer información del AST
            funciones = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            clases = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            return {
                'compressed': True,
                'type': 'python',
                'functions': funciones,
                'classes': clases,
                'ast_dump': ast.dump(tree)[:200] + '...',  # Primeros 200 chars
                'size_original': len(codigo_fuente)
            }
        else:
            # Para otros archivos, usar compresión simple
            return {
                'compressed': True,
                'type': 'text',
                'size_original': len(codigo_fuente),
                'preview': codigo_fuente[:100] + '...'
            }
    except Exception as e:
        return {
            'compressed': False,
            'error': str(e),
            'size_original': len(codigo_fuente)
        }


def main():
    print("=" * 80)
    print("🔧 EJEMPLO ANTONIO - PASO 3: COMPRESIÓN CON AST")
    print("=" * 80)
    print()
    
    # Configuración
    GITHUB_TOKEN = "ghp_xxxxxxxxxxxxx"  # Reemplazar con token real
    REPOSITORY = "usuario/repositorio"   # Reemplazar con repo real
    
    print("📥 Paso 1: Recibir archivos de Andre (Paso 2)")
    print(f"   Repository: {REPOSITORY}")
    print(f"   Token: {GITHUB_TOKEN[:10]}...")
    print()
    
    # Llamar a la herramienta de Andre
    result = fetch_github_repo_tool(
        repository=REPOSITORY,
        github_token=GITHUB_TOKEN,
        extensions=None  # Filtrado inteligente automático
    )
    
    # Verificar resultado
    if result['status'] != 'success':
        print(f"❌ Error: {result['message']}")
        return
    
    print(f"✅ {result['file_count']} archivos recibidos de Andre")
    print()
    
    # Paso 2: Comprimir con AST
    print("🔄 Paso 2: Comprimiendo archivos con AST...")
    print()
    
    archivos_comprimidos = []
    
    for i, file in enumerate(result['files'], 1):
        print(f"   [{i}/{result['file_count']}] Procesando: {file['path']}")
        
        # Comprimir con AST
        compressed = comprimir_con_ast(file['content'], file['path'])
        
        # Guardar resultado
        archivos_comprimidos.append({
            'path': file['path'],
            'size_original': file['size'],
            'dependencies': file['dependencies'],
            'compressed_data': compressed
        })
    
    print()
    print(f"✅ {len(archivos_comprimidos)} archivos comprimidos")
    print()
    
    # Paso 3: Guardar para Uriel (Paso 4)
    output_file = 'archivos_para_uriel.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'repository': REPOSITORY,
            'total_files': len(archivos_comprimidos),
            'files': archivos_comprimidos
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📤 Paso 3: Archivo guardado para Uriel")
    print(f"   Archivo: {output_file}")
    print()
    
    # Mostrar estadísticas
    print("📊 Estadísticas:")
    total_original = sum(f['size_original'] for f in archivos_comprimidos)
    archivos_python = sum(1 for f in archivos_comprimidos if f['path'].endswith('.py'))
    
    print(f"   - Total archivos: {len(archivos_comprimidos)}")
    print(f"   - Archivos Python: {archivos_python}")
    print(f"   - Tamaño total: {total_original / 1024:.2f} KB")
    print()
    
    # Mostrar ejemplo de archivo comprimido
    if archivos_comprimidos:
        print("📄 Ejemplo de archivo comprimido:")
        ejemplo = archivos_comprimidos[0]
        print(f"   Path: {ejemplo['path']}")
        print(f"   Tamaño original: {ejemplo['size_original']} bytes")
        print(f"   Dependencias: {ejemplo['dependencies']}")
        print(f"   Comprimido: {ejemplo['compressed_data']['compressed']}")
        print()
    
    print("=" * 80)
    print("✅ PROCESO COMPLETO")
    print("=" * 80)
    print()
    print("📋 Próximos pasos:")
    print("   1. ✅ Andre extrajo el repositorio (Paso 2)")
    print("   2. ✅ Antonio comprimió con AST (Paso 3)")
    print("   3. ⏭️  Uriel analizará con IBM Bob (Paso 4)")
    print("   4. ⏭️  Gio formateará a Markdown (Paso 5)")
    print("   5. ⏭️  Rafiki mostrará al usuario (Frontend)")
    print()


if __name__ == "__main__":
    main()

# Made with Bob

"""
Conexión entre para_uriel.json (Antonio) y motor.py (Uriel)
============================================================
Lee para_uriel.json de compression_path y genera paraGio.json
"""

import sys
from pathlib import Path
import json

# Agregar raíz del proyecto al path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.api.motor import GraniteAnalyzer

def generar_analisis(project_name: str = "Unknown Project"):
    """
    Lee para_uriel.json y genera paraGio.json con el análisis AI
    
    Args:
        project_name: Nombre del proyecto
        
    Returns:
        Diccionario con el análisis
    """
    # Rutas (para_uriel.json está en la raíz de Hackathon-IBM-ODST)
    input_file = str(project_root / "para_uriel.json")
    output_file = str(project_root / "conexiones" / "paraGio.json")
    # Crear analizador
    analyzer = GraniteAnalyzer()
    
    # Analizar
    analysis = analyzer.analyze_from_file(
        input_file_path=input_file,
        project_name=project_name
    )
    
    # Guardar resultado
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Análisis guardado en: {output_file}")
    
    return analysis


if __name__ == "__main__":
    # Ejecutar análisis
    result = generar_analisis("Pagina-web")
    print("\n📊 Análisis completado")

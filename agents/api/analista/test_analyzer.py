"""
Script de prueba para el motor de análisis Granite
"""

from motor import GraniteAnalyzer

def test_analysis():
    """Prueba del analizador"""
    print("Iniciando análisis con Granite-4-h-small...")

    analyzer = GraniteAnalyzer()
    result = analyzer.analyze_from_file(
        input_file_path="test_input.json",
        project_name="Sistema de Gestión de Usuarios e Imágenes"
    )

    analyzer.save_analysis(result, "test_output.json")
    print("Análisis completado y guardado en test_output.json")


test_analysis()

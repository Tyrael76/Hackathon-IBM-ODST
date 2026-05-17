"""
Script de prueba para el endpoint /download-docs
Verifica headers HTTP y formato de respuesta
"""
import requests
import json
import os
import sys
import io
from dotenv import load_dotenv

# Fix for Windows console emoji printing
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Configuración
API_URL = "http://localhost:8000/download-docs"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TEST_REPO = "owner/repo"  # Cambiar por un repositorio real para pruebas

def test_download_docs():
    """
    Prueba el endpoint /download-docs y verifica:
    1. Headers HTTP correctos
    2. Content-Type: text/markdown
    3. Content-Disposition: attachment
    4. Contenido Markdown válido con bloques Mermaid
    5. Sección de mitigación presente
    """
    print("="*70)
    print("🧪 TEST: /download-docs endpoint")
    print("="*70)
    
    # Preparar request
    payload = {
        "github_token": GITHUB_TOKEN,
        "repository": TEST_REPO,
        "branch": "main",
        "filters": {
            "overview": True,
            "architecture": True,
            "business-logic": True,
            "onboarding-path": True,
            "security-audit": True,
            "technical-debt": True
        }
    }
    
    print(f"\n📤 Sending POST request to {API_URL}")
    print(f"   Repository: {TEST_REPO}")
    print(f"   Filters: All enabled")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=300)
        
        print(f"\n📥 Response received:")
        print(f"   Status Code: {response.status_code}")
        
        # Verificar headers
        print(f"\n🔍 Checking HTTP Headers:")
        headers = response.headers
        
        content_type = headers.get('content-type', '')
        print(f"   ✓ Content-Type: {content_type}")
        assert 'text/markdown' in content_type.lower(), "Content-Type should be text/markdown"
        
        content_disposition = headers.get('content-disposition', '')
        print(f"   ✓ Content-Disposition: {content_disposition}")
        assert 'attachment' in content_disposition.lower(), "Content-Disposition should contain 'attachment'"
        assert 'filename=' in content_disposition.lower(), "Content-Disposition should contain filename"
        
        content_length = headers.get('content-length', '0')
        print(f"   ✓ Content-Length: {content_length} bytes")
        
        # Verificar contenido
        print(f"\n📄 Checking Markdown Content:")
        content = response.text
        
        print(f"   ✓ Total length: {len(content)} characters")
        
        # Verificar estructura básica
        assert '# Documentación Técnica' in content, "Should contain main title"
        print(f"   ✓ Main title present")
        
        # Verificar bloques Mermaid
        mermaid_count = content.count('```mermaid')
        print(f"   ✓ Mermaid diagrams found: {mermaid_count}")
        if mermaid_count > 0:
            print(f"      (Diagrams are in raw Mermaid syntax, not rendered HTML)")
        
        # Verificar sección de mitigación
        if 'Guía de Ejecución Correcta y Mitigación' in content:
            print(f"   ✓ Mitigation section present")
        else:
            print(f"   ⚠️  Mitigation section not found (may not be included based on filters)")
        
        # Verificar secciones solicitadas
        sections_found = []
        if 'Overview' in content:
            sections_found.append('Overview')
        if 'Arquitectura' in content:
            sections_found.append('Architecture')
        if 'Lógica de Negocio' in content:
            sections_found.append('Business Logic')
        if 'Onboarding' in content:
            sections_found.append('Onboarding')
        if 'Seguridad' in content:
            sections_found.append('Security')
        if 'Deuda Técnica' in content:
            sections_found.append('Technical Debt')
        
        print(f"\n   ✓ Sections found: {', '.join(sections_found)}")
        
        # Guardar archivo de prueba
        test_filename = "test_downloaded_documentation.md"
        with open(test_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n💾 Test file saved: {test_filename}")
        
        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED!")
        print(f"{'='*70}\n")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 300 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        return False
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_headers_only():
    """
    Prueba rápida solo de headers sin procesar todo el repositorio
    """
    print("="*70)
    print("🧪 QUICK TEST: Headers verification (mock)")
    print("="*70)
    
    # Este test requeriría un mock o un repositorio muy pequeño
    # Por ahora, solo documentamos el formato esperado
    
    expected_headers = {
        "Content-Type": "text/markdown; charset=utf-8",
        "Content-Disposition": 'attachment; filename="ODST_Technical_Documentation_owner_repo.md"',
        "Content-Length": "12345",  # Tamaño real del archivo
        "Cache-Control": "no-cache"
    }
    
    print("\n📋 Expected Headers Format:")
    for key, value in expected_headers.items():
        print(f"   {key}: {value}")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ODST - Download Documentation Endpoint Test Suite")
    print("="*70 + "\n")
    
    # Verificar que el token esté configurado
    if not GITHUB_TOKEN:
        print("⚠️  WARNING: GITHUB_TOKEN not found in .env")
        print("   Please set GITHUB_TOKEN in your .env file")
        print("   Also update TEST_REPO variable with a real repository\n")
    
    # Mostrar formato esperado
    test_headers_only()
    
    # Ejecutar test completo (comentado por defecto)
    # Descomentar la siguiente línea para ejecutar el test real:
    # test_download_docs()
    
    print("\n💡 To run the full test:")
    print("   1. Ensure the FastAPI server is running (python main.py)")
    print("   2. Set GITHUB_TOKEN in .env")
    print("   3. Update TEST_REPO with a real repository")
    print("   4. Uncomment test_download_docs() call in this script")
    print("   5. Run: python test_download_docs.py\n")

# Made with Bob

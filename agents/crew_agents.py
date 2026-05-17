import os
import json
from typing import Any, List, Optional, Dict
from pydantic import PrivateAttr
from crewai import Agent, Task, Crew, Process
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain.llms.base import LLM
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

load_dotenv()

# Cache global para evitar llamadas duplicadas
_llm_cache = {}

class CustomWatsonxLLM(LLM):
    model_id: str
    
    def __init__(self, model_id: str, **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        api_key = os.getenv("WATSONX_API_KEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        url = os.getenv("WATSONX_URL")

        credentials = {
            "url": url,
            "apikey": api_key
        }

        model_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 1500,  # Reducido de 4000 a 1500 para respuestas más rápidas
            GenParams.MIN_NEW_TOKENS: 50,    # Aumentado de 10 a 50 para respuestas más concisas
            GenParams.TEMPERATURE: 0.1,
            GenParams.TOP_K: 50,
            GenParams.TOP_P: 0.95,
            GenParams.REPETITION_PENALTY: 1.1
        }

        # Usar object.__setattr__ para evitar problemas con Pydantic
        object.__setattr__(self, '_model', Model(
            model_id=model_id,
            params=model_params,
            credentials=credentials,
            project_id=project_id
        ))

    @property
    def _llm_type(self) -> str:
        return "custom_watsonx"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        # Implementar caché simple basado en hash del prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        if prompt_hash in _llm_cache:
            print(f"✅ Cache hit for prompt hash: {prompt_hash[:8]}...")
            return _llm_cache[prompt_hash]
        
        response = self._model.generate_text(prompt=prompt)
        if isinstance(response, list):
            result = " ".join(str(item) for item in response)
        else:
            result = str(response)
        
        # Guardar en caché
        _llm_cache[prompt_hash] = result
        return result

# Instantiate models based on requirements - usando modelos disponibles
# granite-8b-code-instruct es usado porque 3-1-8b-base no soporta text generation
auditor_llm = CustomWatsonxLLM(model_id="ibm/granite-8b-code-instruct")
writer_llm = CustomWatsonxLLM(model_id="ibm/granite-8b-code-instruct")

def run_crew_analysis(ast_data: dict, filters: dict) -> List[Dict[str, Any]]:
    auditor = Agent(
        role='Auditor Técnico Senior',
        goal='Analizar el AST de un repositorio para extraer su arquitectura, reglas de negocio, vulnerabilidades (OWASP Top 10, tokens expuestos) y deuda técnica.',
        backstory='Eres un arquitecto de software y experto en ciberseguridad. Te enfocas en descubrir vulnerabilidades OWASP, tokens expuestos y cazar antipatrones de diseño.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=auditor_llm
    )

    writer = Agent(
        role='Escritor Técnico Senior',
        goal='Consolidar reportes técnicos. Para secciones de arquitectura, DEBES generar un diagrama de flujo de datos en sintaxis Mermaid.js encapsulado en un bloque de código ```mermaid.',
        backstory='Eres un redactor técnico experto en formato Markdown y visualización de datos usando Mermaid.js.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=writer_llm
    )

    # Crear un resumen compacto del AST en lugar de enviar todo
    ast_summary = _create_ast_summary(ast_data)
    
    results = []
    
    # Preparar todas las tareas para ejecución paralela
    tasks_to_execute = []
    
    if filters.get("overview", False):
        tasks_to_execute.append(("overview", writer, f"Analiza el siguiente resumen del proyecto y proporciona un 'Overview' general de sus tecnologías principales:\n\n{ast_summary}\n\nEntrega el resultado en Markdown.", 1))

    if filters.get("architecture", False):
        arch_prompt = (
            f"Analiza la siguiente estructura del proyecto y deduce la arquitectura.\n"
            f"DEBES seguir este formato estrictamente en Markdown:\n\n"
            f"## Descripción General\n"
            f"(Breve párrafo descriptivo de la arquitectura)\n\n"
            f"## Componentes Principales\n"
            f"(Lista con viñetas de los componentes clave)\n\n"
            f"## Diagrama de Arquitectura\n"
            f"(DEBES crear un diagrama de flujo usando sintaxis Mermaid.js encapsulado en un bloque ```mermaid)\n\n"
            f"Estructura:\n{ast_summary}"
        )
        tasks_to_execute.append(("architecture", writer, arch_prompt, 2))

    if filters.get("business-logic", False):
        tasks_to_execute.append(("business-logic", auditor, f"Analiza el siguiente resumen y extrae los procesos core, entidades y antipatrones detectados:\n\n{ast_summary}\n\nEntrega el resultado estructurado en Markdown.", 3))

    if filters.get("onboarding-path", False):
        tasks_to_execute.append(("onboarding-path", writer, f"Analiza el siguiente resumen y proporciona un 'Onboarding Path' recomendando qué archivos leer primero:\n\n{ast_summary}\n\nEntrega el resultado en Markdown.", 4))

    if filters.get("security-audit", False):
        tasks_to_execute.append(("security-audit", auditor, f"Analiza el siguiente resumen enfocándote en ciberseguridad. Busca vulnerabilidades OWASP Top 10 y secretos expuestos:\n\n{ast_summary}\n\nEntrega el resultado en Markdown.", 5))

    if filters.get("technical-debt", False):
        tasks_to_execute.append(("technical-debt", auditor, f"Analiza el siguiente resumen identificando malas prácticas, antipatrones y deuda técnica con sugerencias de refactorización:\n\n{ast_summary}\n\nEntrega el resultado en Markdown.", 6))
    
    # Ejecutar todas las tareas en paralelo usando ThreadPoolExecutor
    if tasks_to_execute:
        print(f"\n{'='*70}")
        print(f"🤖 [CREW] Starting parallel analysis with {len(tasks_to_execute)} tasks")
        print(f"{'='*70}\n")
        
        with ThreadPoolExecutor(max_workers=min(len(tasks_to_execute), 4)) as executor:
            future_to_task = {}
            for task_info in tasks_to_execute:
                slug, agent, description, order = task_info
                print(f"📋 [CREW] Submitting task: {slug}")
                prompt = f"System: {agent.backstory}\n\nTask: {description}"
                
                try:
                    # Usar el método invoke del LLM directamente
                    future = executor.submit(agent.llm.invoke, prompt)
                    future_to_task[future] = (slug, order)
                except Exception as submit_error:
                    print(f"❌ [CREW] Failed to submit task {slug}: {str(submit_error)}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Error submitting task: {str(submit_error)}",
                        "data": {}
                    })
            
            for future in as_completed(future_to_task):
                slug, order = future_to_task[future]
                try:
                    print(f"⏳ [CREW] Waiting for result: {slug}")
                    response = future.result(timeout=120)  # 2 minutos timeout
                    print(f"✅ [CREW] Completed: {slug}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": str(response),
                        "data": {}
                    })
                except TimeoutError:
                    print(f"⏱️ [CREW] Timeout for task: {slug}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Task timed out after 120 seconds",
                        "data": {}
                    })
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"❌ [CREW] Error in {slug}:")
                    print(f"   Type: {type(e).__name__}")
                    print(f"   Message: {str(e)}")
                    print(f"   Traceback:\n{error_trace}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Error generating report: {str(e)}\n\nDetails:\n{error_trace}",
                        "data": {}
                    })
        
        print(f"\n{'='*70}")
        print(f"✅ [CREW] All tasks completed: {len(results)} results")
        print(f"{'='*70}\n")
    
    # Ordenar resultados por orden
    results.sort(key=lambda x: x["order"])
    return results

def _create_ast_summary(ast_data: dict, max_chars: int = 5000) -> str:
    """
    Crea un resumen compacto del AST para reducir el tamaño del contexto.
    Extrae solo la información más relevante.
    """
    summary_parts = []
    
    # Extraer estructura de archivos
    if "files" in ast_data:
        file_list = list(ast_data["files"].keys())[:50]  # Primeros 50 archivos
        summary_parts.append(f"Files ({len(ast_data['files'])} total): {', '.join(file_list)}")
    
    # Extraer dependencias principales
    if "dependencies" in ast_data:
        deps = ast_data.get("dependencies", {})
        if deps:
            summary_parts.append(f"Dependencies: {', '.join(list(deps.keys())[:20])}")
    
    # Extraer funciones/clases principales (muestra limitada)
    if "files" in ast_data:
        main_entities = []
        for file_path, file_data in list(ast_data["files"].items())[:10]:
            if isinstance(file_data, dict):
                if "classes" in file_data:
                    main_entities.extend([f"class {c}" for c in list(file_data["classes"].keys())[:3]])
                if "functions" in file_data:
                    main_entities.extend([f"func {f}" for f in list(file_data["functions"].keys())[:3]])
        if main_entities:
            summary_parts.append(f"Main entities: {', '.join(main_entities[:30])}")
    
    summary = "\n\n".join(summary_parts)
    
    # Truncar si es necesario
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n... [TRUNCATED]"
    
    return summary

def generate_full_documentation(ast_data: dict, filters: dict) -> str:
    """
    Genera documentación técnica completa en formato Markdown usando CrewAI con proceso secuencial.
    Incluye una sección de mitigación al final con comandos de remediación.
    
    Args:
        ast_data: Datos del AST del repositorio
        filters: Filtros de secciones a incluir
    
    Returns:
        String con el documento Markdown completo
    """
    print(f"\n{'='*70}")
    print(f"📄 [DOCUMENTATION] Starting full documentation generation")
    print(f"{'='*70}\n")
    
    # Crear agentes
    auditor = Agent(
        role='Auditor Técnico Senior',
        goal='Analizar el AST de un repositorio para extraer su arquitectura, reglas de negocio, vulnerabilidades (OWASP Top 10, tokens expuestos) y deuda técnica.',
        backstory='Eres un arquitecto de software y experto en ciberseguridad. Te enfocas en descubrir vulnerabilidades OWASP, tokens expuestos y cazar antipatrones de diseño.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=auditor_llm
    )

    writer = Agent(
        role='Escritor Técnico Senior',
        goal='Consolidar reportes técnicos. Para secciones de arquitectura, DEBES generar un diagrama de flujo de datos en sintaxis Mermaid.js encapsulado en un bloque de código ```mermaid.',
        backstory='Eres un redactor técnico experto en formato Markdown y visualización de datos usando Mermaid.js.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=writer_llm
    )
    
    # Crear resumen del AST
    ast_summary = _create_ast_summary(ast_data)
    
    # Preparar tareas secuenciales
    tasks = []
    
    # Encabezado del documento
    doc_header = f"# Documentación Técnica - ODST Analysis\n\n"
    doc_header += f"**Generado por:** ODST (Omniscient Documentation & Security Toolkit)\n\n"
    doc_header += f"---\n\n"
    
    if filters.get("overview", False):
        tasks.append(Task(
            description=f"Analiza el siguiente resumen del proyecto y proporciona un 'Overview' general de sus tecnologías principales:\n\n{ast_summary}\n\nEntrega el resultado en Markdown con el título '## Overview'.",
            agent=writer,
            expected_output="Sección Overview en formato Markdown"
        ))
    
    if filters.get("architecture", False):
        arch_prompt = (
            f"Analiza la siguiente estructura del proyecto y deduce la arquitectura.\n"
            f"DEBES seguir este formato estrictamente en Markdown:\n\n"
            f"## Arquitectura del Sistema\n\n"
            f"### Descripción General\n"
            f"(Breve párrafo descriptivo de la arquitectura)\n\n"
            f"### Componentes Principales\n"
            f"(Lista con viñetas de los componentes clave)\n\n"
            f"### Diagrama de Arquitectura\n"
            f"(DEBES crear un diagrama de flujo usando sintaxis Mermaid.js encapsulado en un bloque ```mermaid)\n\n"
            f"Estructura:\n{ast_summary}"
        )
        tasks.append(Task(
            description=arch_prompt,
            agent=writer,
            expected_output="Sección de Arquitectura con diagrama Mermaid en formato Markdown"
        ))
    
    if filters.get("business-logic", False):
        tasks.append(Task(
            description=f"Analiza el siguiente resumen y extrae los procesos core, entidades y antipatrones detectados:\n\n{ast_summary}\n\nEntrega el resultado estructurado en Markdown con el título '## Lógica de Negocio'.",
            agent=auditor,
            expected_output="Sección de Lógica de Negocio en formato Markdown"
        ))
    
    if filters.get("onboarding-path", False):
        tasks.append(Task(
            description=f"Analiza el siguiente resumen y proporciona un 'Onboarding Path' recomendando qué archivos leer primero:\n\n{ast_summary}\n\nEntrega el resultado en Markdown con el título '## Guía de Onboarding'.",
            agent=writer,
            expected_output="Sección de Onboarding Path en formato Markdown"
        ))
    
    if filters.get("security-audit", False):
        tasks.append(Task(
            description=f"Analiza el siguiente resumen enfocándote en ciberseguridad. Busca vulnerabilidades OWASP Top 10 y secretos expuestos:\n\n{ast_summary}\n\nEntrega el resultado en Markdown con el título '## Auditoría de Seguridad'.",
            agent=auditor,
            expected_output="Sección de Auditoría de Seguridad en formato Markdown"
        ))
    
    if filters.get("technical-debt", False):
        tasks.append(Task(
            description=f"Analiza el siguiente resumen identificando malas prácticas, antipatrones y deuda técnica con sugerencias de refactorización:\n\n{ast_summary}\n\nEntrega el resultado en Markdown con el título '## Deuda Técnica'.",
            agent=auditor,
            expected_output="Sección de Deuda Técnica en formato Markdown"
        ))
    
    # Tarea de mitigación (siempre se incluye si hay alguna auditoría)
    if filters.get("security-audit", False) or filters.get("technical-debt", False):
        mitigation_prompt = (
            f"Basándote en el análisis previo del repositorio, genera una sección de mitigación práctica.\n\n"
            f"DEBES seguir este formato estrictamente:\n\n"
            f"## Guía de Ejecución Correcta y Mitigación\n\n"
            f"### Comandos de Remediación\n"
            f"(Proporciona comandos específicos de terminal para resolver problemas detectados)\n\n"
            f"### Recomendaciones de Seguridad\n"
            f"(Lista de mejores prácticas y configuraciones seguras)\n\n"
            f"### Plan de Acción Prioritario\n"
            f"(Pasos ordenados por prioridad para mejorar el código)\n\n"
            f"Contexto del repositorio:\n{ast_summary}"
        )
        tasks.append(Task(
            description=mitigation_prompt,
            agent=writer,
            expected_output="Sección de Mitigación con comandos y recomendaciones en formato Markdown"
        ))
    
    # Ejecutar Crew con proceso secuencial
    if not tasks:
        return doc_header + "\n*No se seleccionaron secciones para generar.*\n"
    
    try:
        print(f"🚀 [DOCUMENTATION] Creating Crew with {len(tasks)} sequential tasks")
        crew = Crew(
            agents=[auditor, writer],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        print(f"⚙️ [DOCUMENTATION] Executing sequential workflow...")
        result = crew.kickoff()
        
        # Consolidar resultado
        if isinstance(result, str):
            full_doc = doc_header + result
        else:
            # Si el resultado es un objeto, intentar extraer el texto
            full_doc = doc_header + str(result)
        
        print(f"✅ [DOCUMENTATION] Documentation generation complete!")
        print(f"   Total length: {len(full_doc)} characters")
        print(f"{'='*70}\n")
        
        return full_doc
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [DOCUMENTATION] Error generating documentation:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        
        # Retornar documento con error
        error_doc = doc_header
        error_doc += f"## Error en Generación\n\n"
        error_doc += f"Se produjo un error al generar la documentación:\n\n"
        error_doc += f"```\n{str(e)}\n```\n\n"
        error_doc += f"### Detalles Técnicos\n\n"
        error_doc += f"```\n{error_trace}\n```\n"
        
        return error_doc

def explain_file_direct(file_path: str, file_content: str) -> str:
    prompt = f"Explica en un párrafo corto y 3 viñetas qué hace exactamente este archivo de código, sus dependencias críticas y si tiene algún antipatrón latente.\n\nArchivo: {file_path}\nContenido:\n{file_content}"
    response = writer_llm.invoke(prompt)
    return response


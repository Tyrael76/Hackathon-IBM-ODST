"""
Small real watsonx.ai connection test.

This test calls watsonx.ai once using watsonx_llm_call().
Run it only when you want to spend a small amount of credits.
# This test calls watsonx.ai and may consume credits.
# Run only when needed.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.api.writer.watsonx_writer_client import watsonx_llm_call


def main() -> None:
    prompt = """
Return only this valid JSON array.
Do not add explanations.
Do not wrap the output in markdown fences.

[
  {
    "title": "Inicio",
    "slug": "overview",
    "order": 1,
    "markdown": "# Inicio\\n## Resumen del proyecto\\nPrueba corta de conexión."
  }
]
"""

    print("Calling watsonx.ai...")
    result = watsonx_llm_call(prompt)

    print("\nMODEL RAW OUTPUT:")
    print("=" * 80)
    print(result)
    print("=" * 80)


if __name__ == "__main__":
    main()
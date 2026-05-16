"""
Analysis engine using IBM Watsonx AI with Granite-4-h-small
Analyzes dependency maps and generates structured project documentation
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

load_dotenv()


class GraniteAnalyzer:
    """Class to analyze code using IBM Watsonx's Granite-4-h-small model"""
    
    def __init__(self):
        """Initialize the analyzer with Watsonx credentials"""
        self.api_key = os.getenv("WATSONX_API_KEY")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.url = os.getenv("WATSONX_URL")
        
        self.credentials = {
            "url": self.url,
            "apikey": self.api_key
        }
        
        self.model_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 4000,
            GenParams.MIN_NEW_TOKENS: 100,
            GenParams.TEMPERATURE: 0.3,
            GenParams.TOP_K: 50,
            GenParams.TOP_P: 0.95,
            GenParams.REPETITION_PENALTY: 1.1
        }
        
        self.model = Model(
            model_id="ibm/granite-4-h-small",
            params=self.model_params,
            credentials=self.credentials,
            project_id=self.project_id
        )
    
    def analyze_from_file(self, input_file_path: str, project_name: str = "Unknown Project") -> Dict[str, Any]:
        """
        Analyze a JSON file with code structure
        
        Args:
            input_file_path: Path to input JSON file
            project_name: Project name
            
        Returns:
            Dictionary with complete analysis
        """
        with open(input_file_path, 'r', encoding='utf-8') as f:
            code_map = json.load(f)
        
        code_map_json = json.dumps(code_map, indent=2, ensure_ascii=False)
        
        prompt = f"""You are an expert software architect. Analyze the following dependency map and code signatures.

CODE MAP:
{code_map_json}

INSTRUCTIONS:
Analyze this dependency map and code signatures. Deduce the data flow, core business logic, and how components interact with each other.

Provide a detailed analysis in JSON format with the following EXACT structure:

{{
  "repo_context": {{
    "repo_url": "",
    "stack": [],
    "entrypoints": [],
    "important_files": [],
    "dependencies": []
  }},
  "overview": "General description of the project and its main purpose",
  "architecture": "Description of the system architecture, design patterns used, and general structure",
  "business_logic": "Detailed explanation of the core business logic, data flow, and how components interact",
  "onboarding_path": "Step-by-step guide for a new developer to understand the project: which files to read first, in what order, and why",
  "setup": "Instructions to set up the development environment and run the project",
  "tests": {{
    "summary": "Summary of recommended testing strategy",
    "normal_cases": ["normal case 1", "normal case 2"],
    "edge_cases": ["edge case 1", "edge case 2"],
    "malicious_cases": ["malicious case 1", "malicious case 2"],
    "privacy_checks": ["privacy check 1", "privacy check 2"]
  }},
  "docker": {{
    "explanation": "Explanation of containerization strategy",
    "dockerfile": "Complete content of recommended Dockerfile",
    "docker_compose": "Complete content of recommended docker-compose.yml"
  }}
}}

IMPORTANT:
- Leave "repo_context" with all empty values as shown above
- Respond ONLY with valid JSON, without any additional text before or after."""

        response = self.model.generate_text(prompt=prompt)
        
        if isinstance(response, str):
            response_text = response.strip()
        elif isinstance(response, list):
            response_text = " ".join(str(item) for item in response).strip()
        elif isinstance(response, dict):
            response_text = json.dumps(response)
        else:
            response_text = str(response).strip()
        
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        json_text = response_text[start_idx:end_idx + 1]
        analysis = json.loads(json_text)
        
        repo_context = analysis.pop("repo_context", {
            "repo_url": "",
            "stack": [],
            "entrypoints": [],
            "important_files": [],
            "dependencies": []
        })
        
        return {
            "project_name": project_name,
            "repo_context": repo_context,
            "bob_response": analysis
        }
    
    def save_analysis(self, analysis: Dict[str, Any], output_file_path: str):
        """Save analysis to a JSON file"""
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"Analysis saved to: {output_file_path}")

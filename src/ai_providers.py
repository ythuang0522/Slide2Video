"""AI providers for generating descriptions from images."""

import base64
import logging
from abc import ABC, abstractmethod

import google.generativeai as genai
import openai

logger = logging.getLogger(__name__)


class APIProvider(ABC):
    """Abstract base class for AI API providers."""
    
    @abstractmethod
    def generate_description(self, image_path: str, prompt: str) -> str:
        """Generate a description for the given image."""
        pass


class GeminiProvider(APIProvider):
    """Gemini API provider implementation."""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def generate_description(self, image_path: str, prompt: str) -> str:
        """Generate description using Gemini API."""
        try:
            image_file = genai.upload_file(path=image_path)
            response = self.model.generate_content([prompt, image_file])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error for {image_path} using model {self.model_name}: {e}")
            raise


class OpenAIProvider(APIProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str, model_name: str = 'gpt-4o-mini'):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def generate_description(self, image_path: str, prompt: str) -> str:
        """Generate description using OpenAI API."""
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_completion_tokens=6000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error for {image_path} using model {self.model_name}: {e}")
            raise


class AIProviderFactory:
    """Factory for creating AI providers."""
    
    @staticmethod
    def create_provider(provider_type: str, api_key: str, model_name: str) -> APIProvider:
        """Create an AI provider based on the specified type."""
        if provider_type == 'gemini':
            return GeminiProvider(api_key, model_name)
        elif provider_type == 'openai':
            return OpenAIProvider(api_key, model_name)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}") 
"""Transcript processing module for generating text descriptions from images."""

import logging
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..ai_providers import AIProviderFactory

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """Handles transcript generation from images using AI providers."""
    
    def __init__(self, ai_provider_type: str, api_key: str, model_name: str, prompt: str, thread_count: int = 4):
        # Store provider configuration instead of instance
        self.ai_provider_type = ai_provider_type
        self.api_key = api_key
        self.model_name = model_name
        self.prompt = prompt
        self.thread_count = thread_count
    
    def _create_ai_provider(self):
        """Create a new AI provider instance for thread-safe operations."""
        return AIProviderFactory.create_provider(
            self.ai_provider_type, 
            self.api_key, 
            self.model_name
        )
    
    def _generate_single_transcript(self, image_path: str, output_dir: Path) -> str:
        """Generate transcript for a single image."""
        basename = Path(image_path).stem
        transcript_path = output_dir / f"{basename}.txt"
        
        logger.info(f"Generating transcript for {basename}...")
        
        # Create a thread-local AI provider instance
        ai_provider = self._create_ai_provider()
        description = ai_provider.generate_description(image_path, self.prompt)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(description)
        
        logger.info(f"Transcript saved to {transcript_path}")
        return str(transcript_path)
    
    def generate_transcripts(self, image_paths: List[str], output_dir: Path) -> List[str]:
        """Generate transcripts for all images using multiple threads."""
        logger.info(f"Generating transcripts using {self.thread_count} threads...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        transcript_paths = []
        
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Submit all tasks
            future_to_image = {
                executor.submit(self._generate_single_transcript, image_path, output_dir): image_path
                for image_path in image_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_image):
                image_path = future_to_image[future]
                try:
                    transcript_path = future.result()
                    transcript_paths.append(transcript_path)
                except Exception as exc:
                    logger.error(f"Error processing {image_path}: {exc}")
                    raise
        
        # Sort transcript paths to maintain order
        transcript_paths.sort()
        
        logger.info(f"Generated {len(transcript_paths)} transcripts")
        return transcript_paths 
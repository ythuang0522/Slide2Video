"""Transcript processing module for generating text descriptions from images."""

import logging
from pathlib import Path
from typing import List

from ..ai_providers import APIProvider

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """Handles transcript generation from images using AI providers."""
    
    def __init__(self, ai_provider: APIProvider, prompt: str):
        self.ai_provider = ai_provider
        self.prompt = prompt
    
    def generate_transcripts(self, image_paths: List[str], output_dir: Path) -> List[str]:
        """Generate transcripts for all images."""
        logger.info("Generating transcripts...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        transcript_paths = []
        for image_path in image_paths:
            basename = Path(image_path).stem
            transcript_path = output_dir / f"{basename}.txt"
            
            logger.info(f"Generating transcript for {basename}...")
            description = self.ai_provider.generate_description(image_path, self.prompt)
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(description)
            
            transcript_paths.append(str(transcript_path))
            logger.info(f"Transcript saved to {transcript_path}")
        
        return transcript_paths 
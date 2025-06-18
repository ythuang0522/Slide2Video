"""Transcript polishing module for improving narrative flow between slides."""

import logging
import re
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..ai_providers import AIProviderFactory

logger = logging.getLogger(__name__)


class TranscriptPolisher:
    """Handles transcript polishing using previous slide context for improved narrative flow."""
    
    def __init__(self, ai_provider_type: str, api_key: str, model_name: str, 
                 polishing_prompt: str, first_slide_prompt: str, thread_count: int = 4):
        # Store provider configuration instead of instance for thread safety
        self.ai_provider_type = ai_provider_type
        self.api_key = api_key
        self.model_name = model_name
        self.polishing_prompt = polishing_prompt
        self.first_slide_prompt = first_slide_prompt
        self.thread_count = thread_count
    
    def _create_ai_provider(self):
        """Create a new AI provider instance for thread-safe operations."""
        return AIProviderFactory.create_provider(
            self.ai_provider_type, 
            self.api_key, 
            self.model_name
        )
    
    def _extract_slide_number(self, filepath: str) -> int:
        """Extract slide number from filename like 'slide_01.txt' or 'transcript_slide_01.txt'."""
        filename = Path(filepath).name
        match = re.search(r'slide_(\d+)', filename)
        if match:
            return int(match.group(1))
        else:
            # Fallback: try to extract any number from filename
            match = re.search(r'(\d+)', filename)
            if match:
                return int(match.group(1))
            else:
                raise ValueError(f"Could not extract slide number from filename: {filename}")
    
    def _load_all_transcripts(self, transcript_paths: List[str]) -> Dict[int, str]:
        """Load all transcript files into memory indexed by slide number."""
        logger.info("Loading all transcripts into memory...")
        
        all_content = {}
        
        for transcript_path in transcript_paths:
            try:
                slide_number = self._extract_slide_number(transcript_path)
                
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                all_content[slide_number] = content
                logger.debug(f"Loaded slide {slide_number}: {len(content)} characters")
                
            except Exception as e:
                logger.error(f"Error loading transcript {transcript_path}: {e}")
                raise
        
        logger.info(f"Loaded {len(all_content)} transcripts into memory")
        return all_content
    
    def _format_polishing_prompt(self, previous_content: str, current_content: str) -> str:
        """Format the polishing prompt with context from previous slide."""
        return self.polishing_prompt.format(
            previous_content=previous_content or "[This is the first slide]",
            current_content=current_content
        )
    
    def _format_first_slide_prompt(self, current_content: str) -> str:
        """Format the special prompt for the first slide."""
        return self.first_slide_prompt.format(current_content=current_content)
    
    def _polish_single_transcript(self, slide_number: int, all_original_content: Dict[int, str], 
                                  output_dir: Path) -> str:
        """Polish a single transcript using previous slide context."""
        logger.info(f"Polishing slide {slide_number:02d}...")
        
        # Get context from original (non-polished) content
        current_content = all_original_content[slide_number]
        
        # Use special prompt for first slide, regular polishing for others
        if slide_number == 1:
            formatted_prompt = self._format_first_slide_prompt(current_content)
            logger.info(f"Using first slide special prompt for slide {slide_number:02d}")
        else:
            previous_content = all_original_content.get(slide_number - 1, "")
            formatted_prompt = self._format_polishing_prompt(previous_content, current_content)
            logger.info(f"Using regular polishing prompt for slide {slide_number:02d}")
        
        try:
            # Create thread-local AI provider instance
            ai_provider = self._create_ai_provider()
            
            # Generate polished content (note: no image needed for text polishing)
            # We'll pass an empty string as image_path since we're only doing text processing
            polished_content = ai_provider.generate_description("", formatted_prompt)
            
            # Save polished transcript
            output_filename = f"polished_slide_{slide_number:02d}.txt"
            output_path = output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(polished_content)
            
            logger.info(f"Polished transcript saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error polishing slide {slide_number}: {e}")
            # Fallback: save original content to polished file
            logger.warning(f"Using original content for slide {slide_number} due to polishing failure")
            
            output_filename = f"polished_slide_{slide_number:02d}.txt"
            output_path = output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            
            return str(output_path)
    
    def polish_transcripts(self, transcript_paths: List[str], output_dir: Path) -> List[str]:
        """Polish all transcripts using previous slide context with parallel processing."""
        logger.info(f"Starting transcript polishing using {self.thread_count} threads...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pre-load all transcripts into memory
        all_original_content = self._load_all_transcripts(transcript_paths)
        
        polished_paths = []
        
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Submit all polishing tasks
            future_to_slide = {
                executor.submit(
                    self._polish_single_transcript, 
                    slide_number, 
                    all_original_content, 
                    output_dir
                ): slide_number
                for slide_number in all_original_content.keys()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_slide):
                slide_number = future_to_slide[future]
                try:
                    polished_path = future.result()
                    polished_paths.append(polished_path)
                except Exception as exc:
                    logger.error(f"Error processing slide {slide_number}: {exc}")
                    raise
        
        # Sort polished paths to maintain order
        polished_paths.sort()
        
        logger.info(f"Successfully polished {len(polished_paths)} transcripts")
        return polished_paths 
"""Main pipeline orchestrator for PDF to Video conversion."""

import glob
import logging
from pathlib import Path
from typing import List, Optional

from .config import Config
from .processors.pdf_processor import PDFProcessor
from .processors.transcript_processor import TranscriptProcessor
from .processors.audio_processor import AudioProcessor
from .processors.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class PDF2VideoPipeline:
    """Main pipeline orchestrator for PDF to video conversion."""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_processors()
        self._ensure_directories()
    
    def _setup_processors(self):
        """Initialize all processors with configuration."""
        # AI Provider configuration
        if self.config.api_provider == 'gemini':
            api_key = self.config.gemini_api_key
            model_name = self.config.gemini_model
        else:
            api_key = self.config.openai_api_key
            model_name = self.config.openai_model
        
        logger.info(f"Using {self.config.api_provider} model: {model_name}")
        
        # Initialize processors
        self.pdf_processor = PDFProcessor(dpi=self.config.image_dpi)
        
        self.transcript_processor = TranscriptProcessor(
            ai_provider_type=self.config.api_provider,
            api_key=api_key,
            model_name=model_name,
            prompt=self.config.voiceover_prompt,
            thread_count=self.config.thread_count
        )
        
        self.audio_processor = AudioProcessor(
            language_code=self.config.tts_language,
            voice_name=self.config.tts_voice,
            voice_gender=self.config.tts_voice_gender,
            audio_format=self.config.audio_format,
            is_chirp3_voice=self.config.is_chirp3_voice,
            thread_count=self.config.thread_count
        )
        
        self.video_processor = VideoProcessor(
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
    
    def _ensure_directories(self):
        """Create all necessary output directories."""
        self.config.ensure_output_dirs()
    
    def run_full_pipeline(self) -> tuple[str, str]:
        """Run the complete PDF to video conversion pipeline."""
        try:
            logger.info("Starting PDF to Video pipeline...")
            
            # Step 1: Convert PDF to images
            image_paths = self.convert_pdf_to_images()
            
            # Step 2: Generate transcripts
            transcript_paths = self.generate_transcripts(image_paths)
            
            # Step 3: Generate audio
            audio_paths = self.generate_audio(transcript_paths)
            
            # Step 4: Create video
            video_path, subtitle_path = self.create_video(image_paths, audio_paths, transcript_paths)
            
            logger.info("✅ Pipeline completed successfully!")
            return video_path, subtitle_path
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def convert_pdf_to_images(self) -> List[str]:
        """Convert PDF pages to PNG images."""
        return self.pdf_processor.convert_to_images(
            self.config.input_pdf, 
            self.config.images_dir
        )
    
    def generate_transcripts(self, image_paths: Optional[List[str]] = None) -> List[str]:
        """Generate transcripts for images."""
        if image_paths is None:
            image_paths = sorted(glob.glob(str(self.config.images_dir / "*.png")))
        
        return self.transcript_processor.generate_transcripts(
            image_paths, 
            self.config.transcripts_dir
        )
    
    def generate_audio(self, transcript_paths: Optional[List[str]] = None) -> List[str]:
        """Generate audio files from transcripts."""
        if transcript_paths is None:
            transcript_paths = sorted(glob.glob(str(self.config.transcripts_dir / "*.txt")))
        
        return self.audio_processor.generate_audio_files(
            transcript_paths, 
            self.config.audio_dir
        )
    
    def create_video(self, image_paths: Optional[List[str]] = None, 
                    audio_paths: Optional[List[str]] = None,
                    transcript_paths: Optional[List[str]] = None) -> tuple[str, str]:
        """Create final video with subtitles."""
        if image_paths is None:
            image_paths = sorted(glob.glob(str(self.config.images_dir / "*.png")))
        
        if audio_paths is None:
            audio_paths = sorted(glob.glob(str(self.config.audio_dir / f"*.{self.config.audio_format}")))
        
        if transcript_paths is None:
            transcript_paths = sorted(glob.glob(str(self.config.transcripts_dir / "*.txt")))
        
        return self.video_processor.create_video_with_subtitles(
            image_paths, 
            audio_paths, 
            transcript_paths, 
            self.config.output_dir
        ) 
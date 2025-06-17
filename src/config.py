"""Configuration management for PDF to Video Converter."""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration management using environment variables."""
    
    def __init__(self, env_file: str = None, input_pdf: str = None, output_dir: str = None, thread_count: int = None):
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # API Configuration
        self.api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # LLM Model Configuration
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Google TTS Configuration
        self.tts_language = os.getenv('TTS_LANGUAGE_CODE', 'en-US')
        self.tts_voice = os.getenv('TTS_VOICE_NAME', 'en-US-Neural2-D')
        self.tts_voice_gender = os.getenv('TTS_VOICE_GENDER', 'NEUTRAL')
        
        # Detect voice type for API compatibility
        self.is_chirp3_voice = 'Chirp3-HD' in self.tts_voice if self.tts_voice else False
        
        # File Configuration - command line arguments override environment variables
        self.input_pdf = input_pdf
        self.output_dir = Path(output_dir)
        
        # Processing Configuration
        self.image_dpi = int(os.getenv('IMAGE_DPI', '200'))
        self.audio_format = os.getenv('AUDIO_FORMAT', 'wav').lower()
        self.video_quality = int(os.getenv('VIDEO_QUALITY', '23'))
        self.thread_count = thread_count or int(os.getenv('THREAD_COUNT', '4'))
        
        # Prompt Configuration
        self.voiceover_prompt = os.getenv('VOICEOVER_PROMPT', 
            'Describe this slide for a presentation voiceover. Be clear, concise, and engaging.')
        
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings."""
        if self.api_provider not in ['gemini', 'openai']:
            raise ValueError(f"Invalid API_PROVIDER: {self.api_provider}")
        
        if self.api_provider == 'gemini' and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when using Gemini API")
        
        if self.api_provider == 'openai' and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI API")
        
        if self.audio_format not in ['wav', 'mp3']:
            raise ValueError(f"Invalid AUDIO_FORMAT: {self.audio_format}")

    @property
    def images_dir(self) -> Path:
        """Get the images output directory."""
        return self.output_dir / "images"
    
    @property
    def transcripts_dir(self) -> Path:
        """Get the transcripts output directory."""
        return self.output_dir / "transcripts"
    
    @property
    def audio_dir(self) -> Path:
        """Get the audio output directory."""
        return self.output_dir / "audio"
    
    def ensure_output_dirs(self):
        """Create all necessary output directories."""
        for dir_path in [self.images_dir, self.transcripts_dir, self.audio_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True) 
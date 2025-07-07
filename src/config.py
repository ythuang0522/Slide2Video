"""Configuration management for PDF to Video Converter."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration management using environment variables."""
    
    def __init__(self, env_file: str = None, input_pdf: str = None, output_dir: str = None, thread_count: int = None, api_provider: str = None):
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # API Configuration - command line argument overrides environment variable
        self.api_provider = api_provider 
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # LLM Model Configuration
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Google TTS Configuration
        self.tts_language = os.getenv('TTS_LANGUAGE_CODE', 'cmn-CN')
        self.tts_voice = os.getenv('TTS_VOICE_NAME', 'cmn-CN-Chirp3-HD-Aoede')
        self.tts_voice_gender = os.getenv('TTS_VOICE_GENDER', 'NEUTRAL')
        self.tts_speaking_rate = float(os.getenv('TTS_SPEAKING_RATE', '1.0'))  # 0.25 to 4.0, where 1.0 is normal speed
        
        # Detect voice type for API compatibility
        self.is_chirp3_voice = 'Chirp3-HD' in self.tts_voice if self.tts_voice else False
        
        # File Configuration - command line arguments override environment variables
        self.input_pdf = input_pdf
        self.output_dir = Path(output_dir)
        
        # Processing Configuration
        self.image_dpi = int(os.getenv('IMAGE_DPI', '200'))
        self.audio_format = os.getenv('AUDIO_FORMAT', 'wav').lower()
        self.video_quality = int(os.getenv('VIDEO_QUALITY', '23'))
        self.video_preset = os.getenv('VIDEO_PRESET', 'medium')
        self.resolution_scale = float(os.getenv('RESOLUTION_SCALE', '1.0'))
        self.thread_count = thread_count or int(os.getenv('THREAD_COUNT', '4'))
        
        # Debug logging for audio format
        logger = logging.getLogger(__name__)
        logger.info(f"Config loaded: TTS_SPEAKING_RATE={self.tts_speaking_rate} ")
        logger.info(f"Config loaded: TTS_VOICE_GENDER={self.tts_voice_gender} ")
        logger.info(f"Config loaded: TTS_VOICE={self.tts_voice} ")
        logger.info(f"Config loaded: TTS_LANGUAGE={self.tts_language} ")
        logger.info(f"Config loaded: AUDIO_FORMAT={self.audio_format} ")
        
        # Voiceover Prompt Configuration
        self.voiceover_prompt = os.getenv('VOICEOVER_PROMPT', 
            '''Describe this slide for a presentation voiceover. Be clear, concise, and engaging.
INSTRUCTIONS:
- For very complex figures, tables, mathematical formula etc., do not have to describe all elements in detail. But you must describe the key elements, main points and key takeaways.
- For simple figures, tables, mathematical formula etc., you can describe them in detail.
- Do not describe the background logo and departmental information unrelated to the slide teaching content.
- Do not write any tone intructions and markdown syntax in the voiceover transcript.''')
        
        # Transcript Polishing Configuration
        self.enable_polishing = os.getenv('ENABLE_POLISHING', 'true').lower() == 'true'
        self.polishing_prompt = os.getenv('POLISHING_PROMPT', '''Polish the current slide voiceover transcript for smooth narrative flow from previous slide voiceover transcript.

PREVIOUS SLIDE VOICEOVER TRANSCRIPT:
{previous_content}

CURRENT SLIDE VOICEOVER TRANSCRIPT (to be polished):
{current_content}

INSTRUCTIONS:
- Improve the CURRENT voiceover transcript while keeping its topic and main focus unchanged
- Keep ALL technical details, information, and main points from the current slide voiceover transcript
- Add smooth transitional phrases at the beginning ONLY if the previous slide voiceover transcript is closely related to the current one
- Add smooth transitional phrases at the end ONLY if the current slide voiceover transcript is closely related to the next slide voiceover transcript
- Add conversational tone with natural punctuation (e.g., !, …, ?)
- Do NOT change the core content or subject matter of the current voiceover transcript
- Return only the polished version of the CURRENT voiceover transcript

POLISHED CURRENT SLIDE VOICEOVER TRANSCRIPT:''')
        
        # First Slide Special Prompt Configuration
        self.first_slide_prompt = os.getenv('FIRST_SLIDE_PROMPT', '''Create an engaging introduction for the first slide of a presentation.

ORIGINAL FIRST SLIDE TRANSCRIPT:
{current_content}

INSTRUCTIONS:
- Understand the main topic from the current transcript and create a brief, engaging introduction that gives students a high-level overview of what they will learn
- Add conversational tone with natural punctuation (e.g., !, …, ?)
- Include a simple daily life example or analogy to make the topic relatable if possible
- Keep it concise (30-60 seconds of speech)
- Focus only on the educational content and learning objectives
- End with a transition like "Let's dive in!" or "Let's get started!" or "Let's start with the first slide." or "Let's go!"

ENGAGING FIRST SLIDE INTRODUCTION:''')
        
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
    
    @property
    def polished_transcripts_dir(self) -> Path:
        """Get the polished transcripts output directory."""
        return self.output_dir / "polished_transcripts"
    
    @property
    def pdf_filename_stem(self) -> str:
        """Get the input PDF filename without extension for naming output files."""
        return Path(self.input_pdf).stem
    
    def ensure_output_dirs(self):
        """Create all necessary output directories."""
        dirs = [self.images_dir, self.transcripts_dir, self.audio_dir, self.output_dir]
        if self.enable_polishing:
            dirs.append(self.polished_transcripts_dir)
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True) 
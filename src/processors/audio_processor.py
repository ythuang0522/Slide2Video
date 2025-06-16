"""Audio processing module for generating speech from text."""

import logging
from pathlib import Path
from typing import List

from google.cloud import texttospeech

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles text-to-speech conversion."""
    
    def __init__(self, language_code: str, voice_name: str, voice_gender: str, 
                 audio_format: str = 'wav', is_chirp3_voice: bool = False):
        self.language_code = language_code
        self.voice_name = voice_name
        self.voice_gender = voice_gender
        self.audio_format = audio_format
        self.is_chirp3_voice = is_chirp3_voice
        self.tts_client = texttospeech.TextToSpeechClient()
    
    def generate_audio_files(self, transcript_paths: List[str], output_dir: Path) -> List[str]:
        """Generate audio files from transcripts."""
        logger.info("Generating audio files...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_paths = []
        for transcript_path in transcript_paths:
            basename = Path(transcript_path).stem
            audio_path = output_dir / f"{basename}.{self.audio_format}"
            
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            logger.info(f"Generating audio for {basename}...")
            
            # Generate audio using TTS
            audio_content = self._synthesize_speech(text)
            
            with open(audio_path, "wb") as f:
                f.write(audio_content)
            
            audio_paths.append(str(audio_path))
            logger.info(f"Audio saved to {audio_path}")
        
        return audio_paths
    
    def _synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech from text using Google TTS."""
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure TTS based on voice type
        voice_params = {'language_code': self.language_code}
        
        if self.is_chirp3_voice:
            # Chirp 3: HD voices configuration
            voice_params['name'] = self.voice_name
            logger.info(f"Using Chirp 3: HD voice: {self.voice_name}")
        else:
            # Neural2 and other traditional voices configuration
            if self.voice_name:
                voice_params['name'] = self.voice_name
                logger.info(f"Using Neural2 voice: {self.voice_name}")
            else:
                # Fallback to gender-based selection for Neural2
                voice_params['ssml_gender'] = getattr(texttospeech.SsmlVoiceGender, self.voice_gender)
                logger.info(f"Using voice gender: {self.voice_gender}")
        
        voice = texttospeech.VoiceSelectionParams(**voice_params)
        
        # Set audio format
        if self.audio_format == 'wav':
            audio_encoding = texttospeech.AudioEncoding.LINEAR16
        else:  # mp3
            audio_encoding = texttospeech.AudioEncoding.MP3
        
        audio_config = texttospeech.AudioConfig(audio_encoding=audio_encoding)
        
        # Generate audio
        try:
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # If Chirp 3: HD voice fails, suggest fallback
            if self.is_chirp3_voice:
                logger.warning("Chirp 3: HD voice failed. Consider using a Neural2 voice as fallback.")
            raise 
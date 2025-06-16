"""Video processing module for creating videos with subtitles."""

import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Dict, Any

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video creation and subtitle generation."""
    
    def __init__(self, fps: int = 24, codec: str = 'libx264', audio_codec: str = 'aac'):
        self.fps = fps
        self.codec = codec
        self.audio_codec = audio_codec
    
    def create_video_with_subtitles(self, image_paths: List[str], audio_paths: List[str], 
                                  transcript_paths: List[str], output_dir: Path) -> tuple[str, str]:
        """Create final video with subtitles."""
        logger.info("Creating final video...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        clips = []
        srt_entries = []
        current_time = 0.0
        
        # Create video clips
        for i, (image_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create video clip
            image_clip = ImageClip(image_path, duration=duration)
            video_clip = image_clip.set_audio(audio_clip)
            clips.append(video_clip)
            
            # Prepare SRT entry
            if i < len(transcript_paths):
                with open(transcript_paths[i], 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                
                start_time = current_time
                end_time = current_time + duration
                
                srt_entries.append({
                    'index': i + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': transcript
                })
                
                current_time = end_time
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips)
        
        # Save video
        video_output_path = output_dir / "final_video.mp4"
        final_video.write_videofile(
            str(video_output_path),
            fps=self.fps,
            codec=self.codec,
            audio_codec=self.audio_codec,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Generate SRT file
        srt_output_path = output_dir / "final_video.srt"
        self._write_srt_file(srt_entries, srt_output_path)
        
        logger.info(f"Video created: {video_output_path}")
        logger.info(f"Subtitles created: {srt_output_path}")
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        
        return str(video_output_path), str(srt_output_path)
    
    def _write_srt_file(self, srt_entries: List[Dict[str, Any]], output_path: Path):
        """Write SRT subtitle file."""
        def format_time(seconds):
            delta = timedelta(seconds=seconds)
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}".replace('.', ',')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in srt_entries:
                f.write(f"{entry['index']}\n")
                f.write(f"{format_time(entry['start'])} --> {format_time(entry['end'])}\n")
                f.write(f"{entry['text']}\n\n") 
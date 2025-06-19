"""Video processing module for creating videos with subtitles."""

import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Dict, Any
import textwrap
import re

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video creation and subtitle generation."""
    
    def __init__(self, fps: int = 24, codec: str = 'libx264', audio_codec: str = 'aac', 
                 transition_break: float = 1.0):
        self.fps = fps
        self.codec = codec
        self.audio_codec = audio_codec
        self.transition_break = transition_break  # seconds of break between slides
    
    def create_video_with_subtitles(self, image_paths: List[str], audio_paths: List[str], 
                                  transcript_paths: List[str], output_dir: Path, 
                                  base_filename: str = "final_video") -> tuple[str, str]:
        """Create final video with subtitles."""
        logger.info("Creating final video...")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        clips = []
        srt_entries = []
        current_time = 0.0
        subtitle_index = 1
        
        # Create video clips
        for i, (image_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # Calculate total clip duration (audio + optional transition break)
            is_last_slide = (i == len(image_paths) - 1)
            total_duration = audio_duration
            if not is_last_slide and self.transition_break > 0:
                total_duration += self.transition_break
            
            # Create video clip - image stays longer if there's a break
            image_clip = ImageClip(image_path, duration=total_duration)
            video_clip = image_clip.set_audio(audio_clip)
            clips.append(video_clip)
            
            # Generate subtitle chunks for this slide
            if i < len(transcript_paths):
                with open(transcript_paths[i], 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                
                # Split transcript into subtitle chunks
                text_chunks = self._split_text_into_subtitle_chunks(transcript)
                
                # Create timed subtitle entries
                chunk_duration = audio_duration / len(text_chunks) if text_chunks else audio_duration
                
                for j, chunk in enumerate(text_chunks):
                    start_time = current_time + (j * chunk_duration)
                    end_time = current_time + ((j + 1) * chunk_duration)
                    
                    # Ensure minimum duration and maximum duration per subtitle
                    actual_duration = end_time - start_time
                    if actual_duration < 1.5:
                        end_time = start_time + 1.5
                    elif actual_duration > 6.0:
                        end_time = start_time + 6.0
                    
                    # Don't exceed the audio duration for this slide
                    end_time = min(end_time, current_time + audio_duration)
                    
                    srt_entries.append({
                        'index': subtitle_index,
                        'start': start_time,
                        'end': end_time,
                        'text': chunk
                    })
                    subtitle_index += 1
            
            # Update current time for next slide
            current_time += total_duration
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips)
        
        # Save video
        video_output_path = output_dir / f"{base_filename}.mp4"
        final_video.write_videofile(
            str(video_output_path),
            fps=self.fps,
            codec=self.codec,
            audio_codec=self.audio_codec,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            # Web-optimized settings for platform compatibility
            ffmpeg_params=[
                '-movflags', '+faststart',  # Enable progressive download
                '-pix_fmt', 'yuv420p',      # Ensure broad compatibility
                '-profile:v', 'main',       # H.264 main profile
                '-level', '4.0',            # H.264 level 4.0
                '-crf', '23',               # Constant Rate Factor for quality
                '-preset', 'medium',        # Encoding speed vs compression
                '-f', 'mp4'                 # Force MP4 container format
            ]
        )
        
        # Generate SRT file
        srt_output_path = output_dir / f"{base_filename}.srt"
        self._write_srt_file(srt_entries, srt_output_path)
        
        logger.info(f"Video created: {video_output_path}")
        logger.info(f"Subtitles created: {srt_output_path}")
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        
        return str(video_output_path), str(srt_output_path)
    
    def _split_text_into_subtitle_chunks(self, text: str, max_chars_per_line: int = 50, 
                                       max_lines: int = 2) -> List[str]:
        """Split text into readable subtitle chunks with guaranteed content preservation."""
        if not text.strip():
            return []
        
        # Clean up text - remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        max_chunk_chars = max_chars_per_line * max_lines
        min_chunk_chars = 15  # Minimum meaningful chunk size
        
        # Simple, reliable approach that preserves all content
        chunks = []
        words = text.split()
        current_chunk = ""
        
        for word in words:
            # Try adding this word to current chunk
            test_chunk = f"{current_chunk} {word}".strip()
            
            if len(test_chunk) <= max_chunk_chars:
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Post-process: merge very short chunks with neighbors if possible
        chunks = self._merge_short_chunks(chunks, max_chunk_chars, min_chunk_chars)
        
        # Format chunks with proper line breaks
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append(self._format_chunk_lines(chunk, max_chars_per_line))
        
        return formatted_chunks
    

    
    def _merge_short_chunks(self, chunks: List[str], max_chars: int, min_chars: int) -> List[str]:
        """Merge very short chunks with neighbors when possible."""
        if len(chunks) <= 1:
            return chunks
        
        merged = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            
            # If current chunk is too short, try to merge with next
            if len(current) < min_chars and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                combined = f"{current} {next_chunk}"
                
                if len(combined) <= max_chars:
                    merged.append(combined)
                    i += 2  # Skip next chunk since we merged it
                    continue
            
            # If current chunk is still too short, try to merge with previous
            if len(current) < min_chars and merged:
                previous = merged[-1]
                combined = f"{previous} {current}"
                
                if len(combined) <= max_chars:
                    merged[-1] = combined
                    i += 1
                    continue
            
            # Can't merge, keep as is
            merged.append(current)
            i += 1
        
        return merged
    
    def _format_chunk_lines(self, chunk: str, max_chars_per_line: int) -> str:
        """Format a chunk with proper line breaks while preserving all content."""
        if len(chunk) <= max_chars_per_line:
            return chunk
        
        # Manual line breaking to ensure no content loss
        words = chunk.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        # Join with newlines, but limit to 2 lines max for subtitle standards
        if len(lines) <= 2:
            return '\n'.join(lines)
        else:
            # If more than 2 lines, try to balance the first two lines
            all_words = chunk.split()
            mid_point = len(all_words) // 2
            
            # Try different split points to find the best balance
            best_split = mid_point
            best_diff = float('inf')
            
            for split_point in range(max(1, mid_point - 3), min(len(all_words), mid_point + 4)):
                line1 = ' '.join(all_words[:split_point])
                line2 = ' '.join(all_words[split_point:])
                
                if len(line1) <= max_chars_per_line and len(line2) <= max_chars_per_line:
                    length_diff = abs(len(line1) - len(line2))
                    if length_diff < best_diff:
                        best_diff = length_diff
                        best_split = split_point
            
            line1 = ' '.join(all_words[:best_split])
            line2 = ' '.join(all_words[best_split:])
            return f"{line1}\n{line2}"
    
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
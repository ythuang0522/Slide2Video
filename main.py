#!/usr/bin/env python3
"""
PDF to Video Converter - Main Entry Point
Converts PDF presentations to narrated videos with subtitles using a modular architecture.
"""

import sys
import argparse
import logging
from pathlib import Path

from src.config import Config
from src.pipeline import PDF2VideoPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Convert PDF presentations to narrated videos')
    parser.add_argument('--step', choices=['all', 'images', 'transcripts', 'audio', 'video'],
                       default='all', help='Which step to run (default: all)')
    parser.add_argument('--config', help='Path to .env config file')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config(env_file=args.config)
        
        # Initialize pipeline
        pipeline = PDF2VideoPipeline(config)
        
        # Execute requested step(s)
        if args.step == 'all':
            video_path, subtitle_path = pipeline.run_full_pipeline()
            logger.info(f"Video created: {video_path}")
            logger.info(f"Subtitles created: {subtitle_path}")
        
        elif args.step == 'images':
            image_paths = pipeline.convert_pdf_to_images()
            logger.info(f"Generated {len(image_paths)} images")
        
        elif args.step == 'transcripts':
            transcript_paths = pipeline.generate_transcripts()
            logger.info(f"Generated {len(transcript_paths)} transcripts")
        
        elif args.step == 'audio':
            audio_paths = pipeline.generate_audio()
            logger.info(f"Generated {len(audio_paths)} audio files")
        
        elif args.step == 'video':
            video_path, subtitle_path = pipeline.create_video()
            logger.info(f"Video created: {video_path}")
            logger.info(f"Subtitles created: {subtitle_path}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
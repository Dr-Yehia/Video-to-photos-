#!/usr/bin/env python3
"""Command-line interface.

Examples:
    python cli.py https://www.youtube.com/watch?v=XXXX -o my_slides
    python cli.py lecture.mp4 --sensitivity high --no-pdf
"""

import argparse
import os
import sys

from slide_extractor import (ExtractorConfig, SlideExtractor, build_pdf,
                             build_zip, download_video)


def main():
    p = argparse.ArgumentParser(
        description="Extract unique slides from a YouTube video (or local "
                    "file) into images + PDF.")
    p.add_argument("source", help="YouTube URL or path to a local video file")
    p.add_argument("-o", "--output", default="slides_output",
                   help="output directory (default: slides_output)")
    p.add_argument("-s", "--sensitivity", choices=["low", "medium", "high"],
                   default="medium", help="extraction sensitivity")
    p.add_argument("-q", "--quality", type=int, default=1080,
                   help="max video height to download (default: 1080)")
    p.add_argument("--no-pdf", action="store_true", help="skip PDF creation")
    p.add_argument("--zip", action="store_true", help="also create a ZIP")
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    def progress(pct, msg):
        sys.stderr.write(f"\r  [{pct * 100:5.1f}%] {msg:<40}")
        sys.stderr.flush()

    if os.path.isfile(args.source):
        video_path = args.source
    else:
        print("Downloading video...")
        info = download_video(args.source, args.output,
                              max_height=args.quality, progress=progress)
        video_path = info["path"]
        print(f"\n  Title: {info['title']}")

    print("Extracting slides...")
    extractor = SlideExtractor(ExtractorConfig.from_sensitivity(args.sensitivity))
    slides = extractor.extract(video_path, os.path.join(args.output, "slides"),
                               progress=progress)
    print(f"\n  {len(slides)} unique slides extracted")

    paths = [s.path for s in slides]
    if not args.no_pdf and paths:
        pdf = build_pdf(paths, os.path.join(args.output, "slides.pdf"))
        print(f"  PDF: {pdf}")
    if args.zip and paths:
        z = build_zip(paths, os.path.join(args.output, "slides.zip"))
        print(f"  ZIP: {z}")


if __name__ == "__main__":
    main()

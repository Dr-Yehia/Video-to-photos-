"""Video-to-Slides: extract unique, fully-written slides from any video.

Open-source building blocks:
  - yt-dlp   : YouTube (and 1000+ sites) video downloading
  - OpenCV   : frame decoding & visual change analysis
  - ImageHash: perceptual-hash de-duplication
  - img2pdf  : lossless image -> PDF assembly
"""

from .extractor import SlideExtractor, ExtractorConfig, Slide
from .downloader import download_video, probe_video
from .pdf_builder import build_pdf, build_zip

__version__ = "2.5.0"
__all__ = [
    "SlideExtractor",
    "ExtractorConfig",
    "Slide",
    "download_video",
    "probe_video",
    "build_pdf",
    "build_zip",
]

"""Assemble extracted slides into a PDF (lossless, via img2pdf) or a ZIP."""

from __future__ import annotations

import os
import zipfile
from typing import List

import img2pdf


def build_pdf(image_paths: List[str], output_path: str) -> str:
    """img2pdf embeds the JPEGs as-is — zero re-compression, zero quality loss."""
    if not image_paths:
        raise ValueError("no images to build a PDF from")
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(image_paths))
    return output_path


def build_zip(image_paths: List[str], output_path: str) -> str:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_STORED) as zf:
        for p in image_paths:
            zf.write(p, arcname=os.path.basename(p))
    return output_path

"""Validation limits for untrusted RFP uploads."""
from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath

from fastapi import HTTPException

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_OCR_PAGES = 40
MAX_OCR_PIXELS = 16_000_000
MAX_EXTRACTED_CHARS = 2_000_000
MAX_DOCX_ENTRIES = 1_000
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCX_COMPRESSION_RATIO = 200
SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


def validate_upload_name(filename: str | None) -> tuple[str, str]:
    """Normalize either Windows or POSIX client paths and validate extension."""
    raw_name = (filename or "upload").replace("\\", "/")
    name = PurePosixPath(raw_name).name or "upload"
    suffix = PurePosixPath(name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(415, "Supported files: PDF, DOCX, TXT, MD")
    return name, suffix


def validate_upload_content(suffix: str, content: bytes) -> None:
    """Reject oversized or mismatched uploads before parsing them."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File must be 25 MB or smaller")
    if suffix == ".pdf" and content[:1024].find(b"%PDF-") < 0:
        raise HTTPException(415, "File content does not match the .pdf extension")
    if suffix == ".docx":
        if not content.startswith(b"PK"):
            raise HTTPException(415, "File content does not match the .docx extension")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = archive.infolist()
                names = {item.filename for item in entries}
                if len(entries) > MAX_DOCX_ENTRIES:
                    raise HTTPException(413, "DOCX archive contains too many files")
                expanded_size = sum(item.file_size for item in entries)
                if expanded_size > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise HTTPException(413, "DOCX archive expands beyond the 50 MB limit")
                for item in entries:
                    if item.file_size and item.file_size / max(item.compress_size, 1) > MAX_DOCX_COMPRESSION_RATIO:
                        raise HTTPException(413, "DOCX archive compression ratio is too high")
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise HTTPException(415, "DOCX archive is missing required document parts")
                if "word/vbaProject.bin" in names:
                    raise HTTPException(415, "Macro-enabled documents are not supported")
        except zipfile.BadZipFile as exc:
            raise HTTPException(415, "Invalid DOCX archive") from exc


def validate_extracted_text(value: str) -> str:
    if len(value) > MAX_EXTRACTED_CHARS:
        raise HTTPException(413, "Extracted document text exceeds the 2 million character limit")
    return value

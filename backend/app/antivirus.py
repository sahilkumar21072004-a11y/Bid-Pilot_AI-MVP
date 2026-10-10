"""Fail-closed ClamAV scanning for uploaded RFP documents."""
from __future__ import annotations

import logging
import socket
import struct

from fastapi import HTTPException

from .config import settings

logger = logging.getLogger("bidpilot.antivirus")
CHUNK_BYTES = 1024 * 1024


def scan_uploaded_file(content: bytes) -> None:
    """Scan bytes with the ClamAV INSTREAM protocol when enabled."""
    if not settings.clamav_enabled:
        if settings.is_production:
            raise HTTPException(503, "Malware scanning is required in production")
        return

    try:
        with socket.create_connection((settings.clamav_host, settings.clamav_port), timeout=10) as connection:
            connection.settimeout(120)
            connection.sendall(b"zINSTREAM\\0")
            for offset in range(0, len(content), CHUNK_BYTES):
                chunk = content[offset : offset + CHUNK_BYTES]
                connection.sendall(struct.pack("!I", len(chunk)))
                connection.sendall(chunk)
            connection.sendall(b"\\0\\0\\0\\0")
            response = bytearray()
            while len(response) < 4096:
                packet = connection.recv(1024)
                if not packet:
                    break
                response.extend(packet)
                if b"\\0" in packet:
                    break
        result = bytes(response).rstrip(b"\\0").decode("utf-8", errors="replace")
    except OSError as exc:
        logger.exception("ClamAV scan failed; rejecting upload")
        raise HTTPException(503, "Malware scanner unavailable; upload rejected") from exc

    if result.endswith(": OK"):
        return
    if "FOUND" in result:
        logger.warning("ClamAV detected malware in an uploaded document")
        raise HTTPException(422, "Upload rejected because malware was detected")
    logger.error("ClamAV returned an invalid scan response")
    raise HTTPException(503, "Malware scanner could not verify the upload")

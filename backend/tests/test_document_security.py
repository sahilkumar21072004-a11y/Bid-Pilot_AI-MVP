import io
import zipfile

import pytest
from fastapi import HTTPException

from app.document_security import (
    MAX_EXTRACTED_CHARS,
    MAX_UPLOAD_BYTES,
    validate_extracted_text,
    validate_upload_content,
    validate_upload_name,
)


def _docx_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return output.getvalue()


def test_upload_name_handles_windows_paths_and_checks_extension() -> None:
    assert validate_upload_name(r"C:\fakepath\rfp.PDF") == ("rfp.PDF", ".pdf")
    with pytest.raises(HTTPException) as error:
        validate_upload_name("malware.exe")
    assert error.value.status_code == 415


def test_upload_content_enforces_size_and_file_signatures() -> None:
    with pytest.raises(HTTPException) as too_large:
        validate_upload_content(".txt", b"x" * (MAX_UPLOAD_BYTES + 1))
    assert too_large.value.status_code == 413

    with pytest.raises(HTTPException) as mismatch:
        validate_upload_content(".pdf", b"not a PDF")
    assert mismatch.value.status_code == 415


def test_docx_requires_valid_archive_and_required_parts() -> None:
    validate_upload_content(".docx", _docx_bytes())
    with pytest.raises(HTTPException) as invalid:
        validate_upload_content(".docx", b"PK but not a zip")
    assert invalid.value.status_code == 415


def test_extracted_text_limit_is_enforced() -> None:
    with pytest.raises(HTTPException) as error:
        validate_extracted_text("x" * (MAX_EXTRACTED_CHARS + 1))
    assert error.value.status_code == 413

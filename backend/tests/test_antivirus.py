import pytest
from fastapi import HTTPException

from app import antivirus


class FakeClamAV:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.sent = bytearray()
        self.timeout = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def sendall(self, payload: bytes) -> None:
        self.sent.extend(payload)

    def recv(self, _size: int) -> bytes:
        response, self.response = self.response, b""
        return response


def test_clamav_ok_scans_upload_with_instream_protocol(monkeypatch) -> None:
    scanner = FakeClamAV(b"stream: OK\0")
    monkeypatch.setattr(antivirus.settings, "clamav_enabled", True)
    monkeypatch.setattr(antivirus.socket, "create_connection", lambda *_args, **_kwargs: scanner)

    antivirus.scan_uploaded_file(b"proposal")
    assert scanner.sent.startswith(b"zINSTREAM\0")
    assert b"\0\0\0\x08proposal\0\0\0\0" in scanner.sent


def test_clamav_infection_rejects_upload(monkeypatch) -> None:
    scanner = FakeClamAV(b"stream: Eicar-Test-Signature FOUND\0")
    monkeypatch.setattr(antivirus.settings, "clamav_enabled", True)
    monkeypatch.setattr(antivirus.socket, "create_connection", lambda *_args, **_kwargs: scanner)

    with pytest.raises(HTTPException) as error:
        antivirus.scan_uploaded_file(b"infected")
    assert error.value.status_code == 422


def test_clamav_unavailable_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(antivirus.settings, "clamav_enabled", True)

    def unavailable(*_args, **_kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(antivirus.socket, "create_connection", unavailable)
    with pytest.raises(HTTPException) as error:
        antivirus.scan_uploaded_file(b"proposal")
    assert error.value.status_code == 503

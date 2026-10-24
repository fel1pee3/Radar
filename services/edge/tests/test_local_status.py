"""Telemetry contention must not kill capture or leak private exception data."""

import json
import sys
from pathlib import Path

import pytest

from radar_edge.errors import EdgeError
from radar_edge.local_status import publish_status, safe_diagnostic


def sharing_error():
    failure = PermissionError(13, "synthetic-private-token", "private-source-path")
    failure.winerror = 5
    return failure


def test_transient_windows_reader_lock_retries_without_partial_status(tmp_path, monkeypatch):
    target = tmp_path / "status.json"
    target.write_text('{"sequence": 1}')
    original = Path.replace
    calls, waits = [], []

    def replace(source, destination):
        calls.append(source)
        if len(calls) <= 2:
            assert json.loads(target.read_text()) == {"sequence": 1}
            raise sharing_error()
        return original(source, destination)

    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr("radar_edge.local_status.sleep", waits.append)
    assert publish_status(target, {"sequence": 2}) == 2
    assert waits == [0.02, 0.02]
    assert json.loads(target.read_text()) == {"sequence": 2}
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("windows_sharing", [True, False])
def test_permanent_access_failure_is_bounded_visible_and_redacted(
    tmp_path, monkeypatch, windows_sharing
):
    target = tmp_path / "status.json"
    target.write_text('{"sequence": 1}')
    calls, waits = [], []

    def replace(*_):
        calls.append(1)
        if windows_sharing:
            raise sharing_error()
        raise PermissionError(13, "synthetic-private-token", "private-source-path")

    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr("radar_edge.local_status.sleep", waits.append)
    with pytest.raises(EdgeError, match="diagnóstico local") as captured:
        publish_status(target, {"sequence": 2})
    assert captured.value.code == "LOCAL_STATUS_WRITE_ERROR"
    diagnostic = safe_diagnostic(captured.value.__cause__)
    assert diagnostic["exceptionType"] == "PermissionError" and diagnostic["errno"] == 13
    serialized = json.dumps(diagnostic)
    assert "synthetic-private-token" not in serialized and "private-source-path" not in serialized
    assert len(calls) == (5 if windows_sharing else 1)
    assert len(waits) == (4 if windows_sharing else 0)
    assert json.loads(target.read_text()) == {"sequence": 1}
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows sharing semantics")
@pytest.mark.parametrize("share", [1, 1 | 2 | 4])
def test_real_windows_reader_lock_is_retried_until_handle_closes(tmp_path, monkeypatch, share):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    target = tmp_path / "status.json"
    target.write_text('{"sequence": 1}')

    def open_reader(share):
        handle = kernel.CreateFileW(str(target), 0x80000000, share, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    # Even SHARE_DELETE does not ensure MoveFileEx replacement of an open destination.
    handle = open_reader(share)
    released = []

    def release(_):
        assert kernel.CloseHandle(handle)
        released.append(True)

    monkeypatch.setattr("radar_edge.local_status.sleep", release)
    try:
        assert publish_status(target, {"sequence": 2}) == 1
        assert released == [True]
    finally:
        if not released:
            kernel.CloseHandle(handle)
    assert publish_status(target, {"sequence": 3}) == 0
    assert json.loads(target.read_text()) == {"sequence": 3}

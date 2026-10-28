"""Read-only DXGI and Direct3D12 capability inventory. No camera or configuration writes."""

import ctypes as ct
import os
from uuid import UUID


def adapters():
    if os.name != "nt":
        raise RuntimeError("DXGI capability inspection requires Windows")

    class Guid(ct.Structure):
        _fields_ = [
            ("data1", ct.c_uint32),
            ("data2", ct.c_uint16),
            ("data3", ct.c_uint16),
            ("data4", ct.c_ubyte * 8),
        ]

    class Luid(ct.Structure):
        _fields_ = [("low", ct.c_uint32), ("high", ct.c_int32)]

    class Description(ct.Structure):
        _fields_ = [
            ("description", ct.c_wchar * 128),
            ("vendor", ct.c_uint32),
            ("device", ct.c_uint32),
            ("subsystem", ct.c_uint32),
            ("revision", ct.c_uint32),
            ("dedicatedVideo", ct.c_size_t),
            ("dedicatedSystem", ct.c_size_t),
            ("sharedSystem", ct.c_size_t),
            ("luid", Luid),
            ("flags", ct.c_uint32),
        ]

    def guid(value):
        return Guid.from_buffer_copy(UUID(value).bytes_le)

    def call(obj, index, result_type, argument_types, *arguments):
        vtable = ct.cast(obj, ct.POINTER(ct.POINTER(ct.c_void_p))).contents
        function = ct.WINFUNCTYPE(result_type, ct.c_void_p, *argument_types)(vtable[index])
        return function(obj, *arguments)

    dxgi = ct.WinDLL("dxgi.dll")
    create = dxgi.CreateDXGIFactory1
    create.argtypes = [ct.POINTER(Guid), ct.POINTER(ct.c_void_p)]
    create.restype = ct.c_int32
    factory = ct.c_void_p()
    iid = guid("770aae78-f26f-4dba-a829-253c83d1b387")
    status = create(ct.byref(iid), ct.byref(factory))
    if status < 0:
        raise RuntimeError("CreateDXGIFactory1 failed: " + hex(status & 0xFFFFFFFF))
    d3d = ct.WinDLL("d3d12.dll").D3D12CreateDevice
    d3d.argtypes = [ct.c_void_p, ct.c_uint32, ct.POINTER(Guid), ct.c_void_p]
    d3d.restype = ct.c_int32
    device_iid = guid("189819f1-1db6-4b57-be54-1821339b85f7")
    results = []
    try:
        for index in range(8):
            adapter = ct.c_void_p()
            status = call(
                factory,
                12,
                ct.c_int32,
                [ct.c_uint32, ct.POINTER(ct.c_void_p)],
                index,
                ct.byref(adapter),
            )
            if status & 0xFFFFFFFF == 0x887A0002:
                break
            if status < 0:
                raise RuntimeError("EnumAdapters1 failed")
            try:
                desc = Description()
                status = call(adapter, 10, ct.c_int32, [ct.POINTER(Description)], ct.byref(desc))
                if status < 0:
                    raise RuntimeError("GetDesc1 failed")
                levels = {}
                if not desc.flags & 2:
                    for name, value in [
                        ("12_2", 0xC200),
                        ("12_1", 0xC100),
                        ("12_0", 0xC000),
                        ("11_1", 0xB100),
                        ("11_0", 0xB000),
                    ]:
                        status = d3d(adapter, value, ct.byref(device_iid), None)
                        levels[name] = {
                            "supported": status >= 0,
                            "hresult": hex(status & 0xFFFFFFFF),
                        }
                results.append(
                    {
                        "dxgiIndex": index,
                        "name": desc.description,
                        "vendorId": hex(desc.vendor),
                        "deviceId": hex(desc.device),
                        "softwareAdapter": bool(desc.flags & 2),
                        "dedicatedVideoBytes": desc.dedicatedVideo,
                        "sharedSystemBytes": desc.sharedSystem,
                        "luid": {"high": desc.luid.high, "low": desc.luid.low},
                        "direct3d12FeatureLevels": levels,
                    }
                )
            finally:
                call(adapter, 2, ct.c_uint32, [])
    finally:
        call(factory, 2, ct.c_uint32, [])
    return results

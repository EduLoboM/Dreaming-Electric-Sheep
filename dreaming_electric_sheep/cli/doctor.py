"""
System diagnostics and C-core health verification (`des doctor`).
"""
import sys
import platform
import importlib.util
from typing import Dict, Any


def run_doctor() -> Dict[str, Any]:
    report = {}

    # 1. CPython Runtime & Architecture
    report["python_version"] = sys.version.split()[0]
    report["python_implementation"] = platform.python_implementation()
    report["platform"] = platform.platform()
    report["architecture"] = platform.machine()
    report["gil_disabled"] = getattr(sys, "_is_gil_enabled", lambda: True)() is False

    # 2. C Core Extension & SIMD
    c_core_loaded = False
    simd_isa = "Scalar Fallback"
    intern_addr = "N/A"
    try:
        from dreaming_electric_sheep import _des_core as core
        if core is not None:
            c_core_loaded = True
            simd_isa = core.get_simd_isa_info()
            intern_addr = hex(core.get_intern_table_address())
    except Exception as exc:
        simd_isa = f"Failed to load ({exc})"

    report["c_core_loaded"] = c_core_loaded
    report["simd_isa"] = simd_isa
    report["intern_table_addr"] = intern_addr

    # 3. Optional High-Performance Runtime Extras
    report["granian_installed"] = importlib.util.find_spec("granian") is not None
    report["uvicorn_installed"] = importlib.util.find_spec("uvicorn") is not None
    report["uvloop_installed"] = importlib.util.find_spec("uvloop") is not None
    report["msgspec_installed"] = importlib.util.find_spec("msgspec") is not None
    report["jinja2_installed"] = importlib.util.find_spec("jinja2") is not None

    return report


def print_doctor_report():
    data = run_doctor()
    
    print("\n" + "=" * 60)
    print("  🐏 DREAMING ELECTRIC SHEEP — SYSTEM DIAGNOSTICS (`des doctor`)")
    print("=" * 60)
    
    print(f"  Python Version:        {data['python_version']} ({data['python_implementation']})")
    print(f"  Platform / OS:         {data['platform']} ({data['architecture']})")
    print(f"  Free-Threaded (NoGIL): {'✅ ACTIVE' if data['gil_disabled'] else '❌ Standard GIL'}")
    
    print("-" * 60)
    print("  C CORE & ACCELERATION:")
    print(f"  Shared libdes_core:    {'✅ LOADED' if data['c_core_loaded'] else '❌ NOT LOADED'}")
    print(f"  Active SIMD ISA:       🚀 {data['simd_isa']}")
    print(f"  Static Intern Table:   {data['intern_table_addr']}")
    
    print("-" * 60)
    print("  ASGI RUNTIMES & DEPENDENCIES:")
    print(f"  Granian (Rust ASGI):   {'✅ Installed' if data['granian_installed'] else '⚠️  Not installed (pip install granian)'}")
    print(f"  uvloop:                {'✅ Installed' if data['uvloop_installed'] else '⚠️  Not installed (pip install uvloop)'}")
    print(f"  msgspec (Fast JSON):   {'✅ Installed' if data['msgspec_installed'] else '⚠️  Not installed'}")
    print(f"  Uvicorn:               {'✅ Installed' if data['uvicorn_installed'] else 'ℹ️  Not installed'}")
    print(f"  Jinja2:                {'✅ Installed' if data['jinja2_installed'] else 'ℹ️  Not installed'}")
    print("=" * 60 + "\n")

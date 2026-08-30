"""
Tests for Phase F: `des` CLI (`new`, `doctor`, `bench`, `run`) and scaffolding templates.
"""
import sys
import tempfile
from pathlib import Path
import pytest
from dreaming_electric_sheep.cli.templates import create_project
from dreaming_electric_sheep.cli.doctor import run_doctor, print_doctor_report
from dreaming_electric_sheep.cli.main import build_parser


def test_cli_templates_minimal():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_mini"
        create_project("test_mini", template="minimal", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "pyproject.toml").exists()
        content = (target / "app.py").read_text()
        assert "Application()" in content
        assert "home()" in content


def test_cli_templates_api():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_api"
        create_project("test_api", template="api", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "tests" / "test_app.py").exists()
        content = (target / "app.py").read_text()
        assert "class Item(Struct, frozen=True):" in content
        assert "create_item" in content


def test_cli_templates_full():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_full"
        create_project("test_full", template="full", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "templates" / "index.html").exists()
        content = (target / "app.py").read_text()
        assert "Container()" in content
        assert "DataService" in content


def test_cli_doctor():
    report = run_doctor()
    assert report["c_core_loaded"] is True
    assert any(isa in report["simd_isa"].upper() for isa in ["AVX", "SSE", "SCALAR", "NEON"])
    assert report["intern_table_addr"].startswith("0x")
    # Verify print_doctor_report runs without error
    print_doctor_report()


def test_cli_parser():
    parser = build_parser()
    # Test new
    args = parser.parse_args(["new", "myproject", "--template", "api"])
    assert args.command == "new"
    assert args.project_name == "myproject"
    assert args.template == "api"

    # Test run
    args = parser.parse_args(["run", "main:app", "--port", "9000", "--reload", "--server", "granian"])
    assert args.command == "run"
    assert args.app == "main:app"
    assert args.port == 9000
    assert args.reload is True
    assert args.server == "granian"

    # Test doctor
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"

    # Test bench
    args = parser.parse_args(["bench", "http://127.0.0.1:8000/", "-d", "3", "-c", "20"])
    assert args.command == "bench"
    assert args.duration == 3
    assert args.concurrency == 20

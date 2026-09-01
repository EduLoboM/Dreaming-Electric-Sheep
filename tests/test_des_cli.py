"""
Comprehensive tests for Dreaming Electric Sheep CLI (`des`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from dreaming_electric_sheep.cli.doctor import run_doctor
from dreaming_electric_sheep.cli.templates import create_project

REPO_ROOT = str(Path(__file__).parent.parent.resolve())


def _get_isolated_env(extra_path: Path | str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    # Clean out parent test runner env variables (conftest.py sets APP_DEFAULT_ROUTER=0, PYTEST_*, etc.)
    for k in list(env.keys()):
        if (
            k.startswith("PYTEST_")
            or k.startswith("COV_")
            or k.startswith("COVERAGE_")
            or k.startswith("APP_")
        ):
            del env[k]
    paths = []
    if extra_path is not None:
        paths.append(str(Path(extra_path).resolve()))
    paths.append(REPO_ROOT)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_des_cmd(
    args: list[str], cwd: Path | str | None = None
) -> subprocess.CompletedProcess[str]:
    """Runs `des` CLI via subprocess for complete process isolation."""
    cmd = [sys.executable, "-m", "dreaming_electric_sheep.cli.main"] + args
    extra = cwd
    if "-C" in args:
        idx = args.index("-C")
        if idx + 1 < len(args):
            extra = args[idx + 1]
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=_get_isolated_env(extra),
        capture_output=True,
        text=True,
    )


def run_pytest_in_dir(target: Path | str) -> subprocess.CompletedProcess[str]:
    """Runs pytest inside a scaffolded project directory with repo PYTHONPATH."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-vv"],
        cwd=target,
        env=_get_isolated_env(target),
        capture_output=True,
        text=True,
    )


def test_cli_no_args_cheat_sheet():
    result = run_des_cmd([])
    assert result.returncode == 0
    assert "Dreaming Electric Sheep CLI (des)" in result.stdout
    assert "Commands:" in result.stdout
    assert "new" in result.stdout
    assert "dev" in result.stdout
    assert "run" in result.stdout
    assert "check" in result.stdout
    assert "routes" in result.stdout
    assert "why" in result.stdout
    assert "doctor" in result.stdout
    assert "bench" not in result.stdout


def test_cli_version():
    result = run_des_cmd(["--version"])
    assert result.returncode == 0
    assert "des (Dreaming Electric Sheep)" in result.stdout


def test_cli_help_no_bench():
    result = run_des_cmd(["--help"])
    assert result.returncode == 0
    assert "bench" not in result.stdout
    assert "new" in result.stdout
    assert "why" in result.stdout


def test_cli_templates_minimal():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_mini"
        create_project("test_mini", template="minimal", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "pyproject.toml").exists()
        assert (target / ".env.example").exists()
        content = (target / "app.py").read_text(encoding="utf-8")
        assert "Application()" in content
        assert "uvicorn.run" not in content

        # Run pytest inside scaffolded project
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_templates_api_docs_scalar():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_api_scalar"
        create_project(
            "test_api_scalar", template="api", docs="scalar", target_dir=target
        )
        app_code = (target / "app.py").read_text(encoding="utf-8")
        assert 'ScalarUIProvider("/docs")' in app_code
        assert 'docs.ui_providers = [ScalarUIProvider("/docs")]' in app_code

        # Run pytest inside scaffolded project
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_templates_api_docs_swagger():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_api_sw"
        create_project("test_api_sw", template="api", docs="swagger", target_dir=target)
        app_code = (target / "app.py").read_text(encoding="utf-8")
        assert 'SwaggerUIProvider("/docs")' in app_code
        assert 'docs.ui_providers = [SwaggerUIProvider("/docs")]' in app_code

        # Run pytest inside scaffolded project
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_templates_api_docs_redoc():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_api_rd"
        create_project("test_api_rd", template="api", docs="redoc", target_dir=target)
        app_code = (target / "app.py").read_text(encoding="utf-8")
        assert 'ReDocUIProvider("/docs")' in app_code
        assert 'docs.ui_providers = [ReDocUIProvider("/docs")]' in app_code

        # Run pytest inside scaffolded project
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_templates_docs_invalid_on_minimal():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_invalid"
        with pytest.raises(SystemExit) as exc:
            create_project(
                "test_invalid", template="minimal", docs="swagger", target_dir=target
            )
        assert exc.value.code == 1


def test_cli_templates_full():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_full"
        create_project("test_full", template="fullstack", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "templates" / "index.html").exists()
        assert (target / "templates" / "partials" / "item_row.html").exists()
        app_code = (target / "app.py").read_text(encoding="utf-8")
        assert "JinjaRenderer" in app_code
        assert "uvicorn.run" not in app_code

        # Run pytest inside scaffolded project
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_templates_htmx():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_htmx"
        create_project("test_htmx", template="htmx", target_dir=target)
        assert (target / "app.py").exists()
        assert (target / "templates" / "index.html").exists()
        res = run_pytest_in_dir(target)
        assert res.returncode == 0, res.stdout + res.stderr


def test_cli_doctor():
    report = run_doctor()
    assert report["c_core_loaded"] is True
    assert any(
        isa in report["simd_isa"].upper() for isa in ["AVX", "SSE", "SCALAR", "NEON"]
    )
    assert report["intern_table_addr"].startswith("0x")
    assert report["intern_singleton_shared"] is True
    assert report["cython_extensions_all_loaded"] is True
    assert report["freeze_implemented"] is False
    assert report["freeze_status"] == "stub (pass)"

    # Test via CLI runner
    result = run_des_cmd(["doctor", "--json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["simd_isa"] == report["simd_isa"]
    assert data["c_core_loaded"] is True


def test_cli_check_routes_why_e2e():
    with tempfile.TemporaryDirectory() as tmpdir:
        api_dir = Path(tmpdir) / "test_e2e"
        res_new = run_des_cmd(["new", "test_e2e", "-t", "api"], cwd=tmpdir)
        assert res_new.returncode == 0

        # des check
        res_check = run_des_cmd(["-C", str(api_dir), "check", "--json"])
        assert res_check.returncode == 0, res_check.stderr
        check_data = json.loads(res_check.stdout)
        assert check_data["status"] == "OK"
        assert check_data["routes_count"] >= 5
        assert check_data["openapi_bound"] is True
        assert check_data["ui_provider"] == "ScalarUIProvider"

        # des routes
        res_routes = run_des_cmd(["-C", str(api_dir), "routes", "--json"])
        assert res_routes.returncode == 0, res_routes.stderr
        routes_data = json.loads(res_routes.stdout)
        paths = [r["path"] for r in routes_data]
        assert "/docs" in paths
        assert "/openapi.json" in paths
        assert "/items/{item_id}" in paths

        # des why matching
        res_why_match = run_des_cmd(
            ["-C", str(api_dir), "why", "GET", "/items/1", "--json"]
        )
        assert res_why_match.returncode == 0, res_why_match.stderr
        why_data = json.loads(res_why_match.stdout)
        assert why_data["status"] == "MATCH"
        assert why_data["matched_pattern"] == "/items/{item_id}"
        assert why_data["path_params"] == {"item_id": "1"}
        assert why_data["handler"] == "app:get_item"

        # des why docs matching
        res_why_docs = run_des_cmd(
            ["-C", str(api_dir), "why", "GET", "/docs", "--json"]
        )
        assert res_why_docs.returncode == 0, res_why_docs.stderr
        why_docs_data = json.loads(res_why_docs.stdout)
        assert why_docs_data["status"] == "MATCH"
        assert why_docs_data["matched_pattern"] == "/docs"

        # des why non-matching -> exit 1
        res_why_nomatch = run_des_cmd(
            ["-C", str(api_dir), "why", "GET", "/nonexistent_url", "--json"]
        )
        assert res_why_nomatch.returncode == 1
        nomatch_data = json.loads(res_why_nomatch.stdout)
        assert nomatch_data["status"] == "NO_MATCH"
        assert len(nomatch_data["nearest_routes"]) > 0


def test_cli_check_failure_on_bad_app():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_app_file = Path(tmpdir) / "bad.py"
        bad_app_file.write_text("raise RuntimeError('Fatal syntax/import failure')")

        res = run_des_cmd(["-C", str(tmpdir), "check", "bad:app", "--json"])
        assert res.returncode == 2
        data = json.loads(res.stdout)
        assert data["status"] == "FAIL"
        assert "Fatal syntax/import failure" in data["error"]

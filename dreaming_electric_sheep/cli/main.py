"""
Command-line interface entry point for Dreaming Electric Sheep (`des`).
"""
import sys
import argparse
import subprocess
import importlib.util
from pathlib import Path
from dreaming_electric_sheep.cli.templates import create_project
from dreaming_electric_sheep.cli.doctor import print_doctor_report
from dreaming_electric_sheep.cli.bench import run_benchmark


def cmd_new(args):
    target = Path.cwd() / args.project_name
    print(f"Creating project {args.project_name!r} with template {args.template!r} in {target}...")
    create_project(args.project_name, template=args.template, target_dir=target)
    print(f"✅ Successfully created {args.project_name}!")
    print(f"\nTo get started:\n  cd {args.project_name}\n  des run\n")


def cmd_run(args):
    app_target = args.app
    host = args.host
    port = args.port
    reload = args.reload
    server = args.server.lower()

    has_granian = importlib.util.find_spec("granian") is not None
    has_uvicorn = importlib.util.find_spec("uvicorn") is not None

    if server == "auto":
        server = "granian" if has_granian else ("uvicorn" if has_uvicorn else "none")

    if server == "granian":
        if not has_granian:
            print("❌ Granian is not installed. Install with `pip install granian` or use `--server uvicorn`.")
            sys.exit(1)
        cmd = ["granian", "--interface", "asgi", "--host", host, "--port", str(port)]
        if reload:
            cmd.append("--reload")
        cmd.append(app_target)
        print(f"🚀 Starting Granian ASGI server on http://{host}:{port} ({app_target})...")
        subprocess.run(cmd)
    elif server == "uvicorn":
        if not has_uvicorn:
            print("❌ Uvicorn is not installed. Install with `pip install uvicorn`.")
            sys.exit(1)
        cmd = ["uvicorn", app_target, "--host", host, "--port", str(port)]
        if reload:
            cmd.append("--reload")
        print(f"🚀 Starting Uvicorn ASGI server on http://{host}:{port} ({app_target})...")
        subprocess.run(cmd)
    else:
        print("❌ No compatible ASGI server found. Please install granian (`pip install granian`) or uvicorn.")
        sys.exit(1)


def cmd_doctor(args):
    print_doctor_report()


def cmd_bench(args):
    run_benchmark(
        url=args.url,
        duration=args.duration,
        concurrency=args.concurrency,
        compare=getattr(args, "compare", False),
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="des",
        description="🐏 Dreaming Electric Sheep — Ultra-Fast ASGI CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # new
    p_new = subparsers.add_parser("new", help="Create a new Dreaming Electric Sheep project")
    p_new.add_argument("project_name", help="Name of the new project / directory")
    p_new.add_argument(
        "--template",
        "-t",
        choices=["minimal", "api", "full"],
        default="minimal",
        help="Project template (default: minimal)",
    )
    p_new.set_defaults(func=cmd_new)

    # run
    p_run = subparsers.add_parser("run", help="Run application server (Granian/Uvicorn)")
    p_run.add_argument("app", nargs="?", default="app:app", help="Application target (default: app:app)")
    p_run.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    p_run.add_argument("--port", "-p", type=int, default=8000, help="Bind port (default: 8000)")
    p_run.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload on code change")
    p_run.add_argument(
        "--server",
        "-s",
        choices=["auto", "granian", "uvicorn"],
        default="auto",
        help="ASGI server backend (default: auto -> granian if installed)",
    )
    p_run.set_defaults(func=cmd_run)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Inspect SIMD, C-core, and environment health")
    p_doc.set_defaults(func=cmd_doctor)

    # bench
    p_bench = subparsers.add_parser("bench", help="Run HTTP load benchmark against endpoint")
    p_bench.add_argument("url", nargs="?", default="http://127.0.0.1:8000/", help="Target URL to benchmark")
    p_bench.add_argument("--duration", "-d", type=int, default=5, help="Test duration in seconds (default: 5)")
    p_bench.add_argument("--concurrency", "-c", type=int, default=50, help="Concurrent connections (default: 50)")
    p_bench.add_argument("--compare", action="store_true", help="Run comparative benchmark harness across ASGI frameworks")
    p_bench.set_defaults(func=cmd_bench)

    return parser


def main():
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

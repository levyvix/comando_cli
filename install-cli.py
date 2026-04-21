#!/usr/bin/env python3
"""Instala comando-cli (com) como CLI global usando UV
Execute com: uv run install-cli.py
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

# Fix encoding para Windows suportar emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def run_command(cmd, check=True, shell=False, cwd=None):
    """Executa comando e mostra output."""
    result = subprocess.run(cmd, check=check, text=True, shell=shell, cwd=cwd)
    return result.returncode == 0


def check_uv_installed() -> bool | None:
    """Verifica se UV está instalado."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv() -> bool:
    """Instala UV automaticamente usando pip."""
    # Tenta pip3 primeiro, depois pip
    pip_cmd = None
    for cmd in ["pip3", "pip"]:
        try:
            subprocess.run([cmd, "--version"], check=True, capture_output=True)
            pip_cmd = cmd
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    if not pip_cmd:
        return False

    # Instala UV via pip
    install_cmd = [pip_cmd, "install", "--user", "uv"]
    if run_command(install_cmd, check=False):
        # Adiciona scripts do Python ao PATH
        if platform.system() == "Windows":
            # Windows: Scripts vai para AppData\Roaming\Python\Python3X\Scripts
            python_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
            scripts_dir = (
                Path.home() / "AppData" / "Roaming" / "Python" / python_version / "Scripts"
            )
            if scripts_dir.exists():
                os.environ["PATH"] = f"{scripts_dir};{os.environ['PATH']}"
        elif platform.system() == "Darwin":
            # macOS: Scripts vai para ~/Library/Python/X.Y/bin
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            scripts_dir = Path.home() / "Library" / "Python" / python_version / "bin"
            if scripts_dir.exists():
                os.environ["PATH"] = f"{scripts_dir}:{os.environ['PATH']}"
        else:
            # Linux: Scripts vai para ~/.local/bin
            scripts_dir = Path.home() / ".local" / "bin"
            if scripts_dir.exists():
                os.environ["PATH"] = f"{scripts_dir}:{os.environ['PATH']}"

        # Se estiver no GitHub Actions, adiciona ao GITHUB_PATH
        if os.getenv("GITHUB_PATH"):
            with open(os.environ.get("GITHUB_PATH"), "a") as f:  # type: ignore
                f.write(f"{scripts_dir}\n")

        return True

    return False


def install_as_cli() -> bool:
    """Instala comando-cli (com) como ferramenta CLI global."""
    # Fonte explícita tem prioridade total (ex.: testes ou mirrors).
    install_source = os.getenv("COMANDO_CLI_INSTALL_SOURCE")
    if install_source:
        if not run_command(["uv", "tool", "install", "--reinstall", install_source]):
            return False
    else:
        repo_url = os.getenv(
            "COMANDO_CLI_REPO_URL", "https://github.com/levyvix/comando_cli.git"
        )
        repo_ref = os.getenv("COMANDO_CLI_REF", "master")

        # Clona o repositório temporariamente e instala usando "." no clone.
        git_available = run_command(["git", "--version"], check=False)
        if git_available:
            with tempfile.TemporaryDirectory() as tmp_dir:
                clone_dir = Path(tmp_dir) / "comando_cli"
                if not run_command(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        "--branch",
                        repo_ref,
                        repo_url,
                        str(clone_dir),
                    ],
                    check=False,
                ):
                    return False
                if not run_command(
                    ["uv", "tool", "install", "--reinstall", "."],
                    cwd=str(clone_dir),
                ):
                    return False
        else:
            # Fallback sem git local.
            fallback_source = f"git+{repo_url}@{repo_ref}"
            if not run_command(["uv", "tool", "install", "--reinstall", fallback_source]):
                return False

    # Adiciona ao GITHUB_PATH se estiver no GitHub Actions
    github_path = os.getenv("GITHUB_PATH")
    if github_path:
        tool_bin = Path.home() / ".local" / "bin"
        if platform.system() == "Windows":
            tool_bin = Path.home() / ".local" / "bin"  # UV tool bin no Windows

        with open(github_path, "a") as f:
            f.write(f"{tool_bin}\n")

    return True


def main() -> None:
    # Verifica/instala UV
    if not check_uv_installed():
        if not install_uv():
            sys.exit(1)

        # Verifica se instalação funcionou
        if not check_uv_installed():
            sys.exit(1)

    # Instala CLI
    if not install_as_cli():
        sys.exit(1)


if __name__ == "__main__":
    main()

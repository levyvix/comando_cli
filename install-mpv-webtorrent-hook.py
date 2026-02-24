#!/usr/bin/env python3
"""Instala mpv-webtorrent-hook para streaming de torrents via mpv.
Execute com: uv run install-mpv-webtorrent-hook.py

Dependências instaladas:
- webtorrent-cli (npm)
- jq
- xidel
- mpv-webtorrent-hook (git clone em ~/.config/mpv/scripts/)
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> bool:
    """Executa comando e retorna sucesso."""
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        print(f"Erro ao executar: {' '.join(cmd)}", file=sys.stderr)
        return False
    return result.returncode == 0


def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def check_dep(name: str) -> bool:
    ok = which(name)
    status = "ok" if ok else "ausente"
    print(f"  {name}: {status}")
    return ok


def install_system_deps() -> bool:
    """Instala jq e xidel via pacman (Arch) ou apt (Debian/Ubuntu)."""
    missing = [dep for dep in ["jq", "xidel"] if not which(dep)]
    if not missing:
        return True

    print(f"Instalando dependências do sistema: {', '.join(missing)}")

    if which("pacman"):
        return run(["sudo", "pacman", "-S", "--noconfirm", *missing])
    elif which("apt-get"):
        return run(["sudo", "apt-get", "install", "-y", *missing])
    elif which("dnf"):
        return run(["sudo", "dnf", "install", "-y", *missing])
    else:
        print(
            "Gerenciador de pacotes não suportado. Instale manualmente: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return False


def install_webtorrent_cli() -> bool:
    """Instala webtorrent-cli via npm."""
    if which("webtorrent"):
        print("  webtorrent-cli: ok")
        return True

    if not which("npm"):
        print("npm não encontrado. Instale Node.js primeiro.", file=sys.stderr)
        return False

    print("Instalando webtorrent-cli via npm...")
    return run(["npm", "install", "-g", "webtorrent-cli"])


def install_hook() -> bool:
    """Clona mpv-webtorrent-hook em ~/.config/mpv/scripts/."""
    scripts_dir = Path.home() / ".config" / "mpv" / "scripts"
    hook_dir = scripts_dir / "webtorrent-hook"

    if hook_dir.exists():
        print(f"  mpv-webtorrent-hook: ok ({hook_dir})")
        print("  Atualizando...")
        return run(["git", "-C", str(hook_dir), "pull"])

    scripts_dir.mkdir(parents=True, exist_ok=True)
    print(f"Clonando mpv-webtorrent-hook em {hook_dir}...")
    return run([
        "git", "clone",
        "https://github.com/noctuid/mpv-webtorrent-hook",
        str(hook_dir),
    ])


def main() -> None:
    print("=== Instalando mpv-webtorrent-hook ===\n")

    print("Verificando dependências:")
    check_dep("mpv")
    check_dep("git")
    check_dep("npm")

    print()

    if not install_system_deps():
        sys.exit(1)

    if not install_webtorrent_cli():
        sys.exit(1)

    if not install_hook():
        sys.exit(1)

    print("\nPronto! mpv agora suporta magnet links diretamente.")
    print("Teste com: mpv 'magnet:?xt=urn:btih:...'")


if __name__ == "__main__":
    main()

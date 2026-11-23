#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Crea el repositorio especial del perfil de GitHub y publica la portada.

En GitHub, el repositorio que se llama igual que el usuario es especial: su README
se muestra en la pagina principal del perfil.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).parent
ENV = Path(r"C:\Users\luis_\AppData\Local\hermes\.env")

token = None
for linea in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
    if linea.strip().startswith("GITHUB_TOKEN="):
        token = linea.split("=", 1)[1].strip()
        break
if not token:
    raise SystemExit("sin token en el .env")


def api(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo else None
    req = urllib.request.Request("https://api.github.com" + ruta, data=datos, method=metodo)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "hermes")
    if datos:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


codigo, usuario = api("GET", "/user")
if codigo != 200:
    raise SystemExit(f"autenticacion fallida: {codigo}")
login = usuario["login"]
print("usuario:", login)

print("\n=== Repositorio especial del perfil ===")
codigo, resp = api("POST", "/user/repos", {
    "name": login,
    "description": "Perfil profesional: ingenieria de operaciones, analitica de datos e IA aplicada",
    "private": False,
    "has_issues": True,
    "has_wiki": False,
    "auto_init": False,
})
if codigo == 201:
    print("  repositorio creado:", resp.get("html_url"))
elif codigo == 422:
    print("  ya existia, se reutiliza")
else:
    print(f"  ERROR {codigo}: {resp.get('message')}")

# git local
env_git = dict(os.environ)
env_git["GIT_TERMINAL_PROMPT"] = "0"
env_git["GCM_INTERACTIVE"] = "never"


def git(args):
    r = subprocess.run(["git", "-c", "credential.helper="] + args, cwd=REPO,
                       capture_output=True, text=True, env=env_git, timeout=180)
    return r.returncode, (r.stdout + r.stderr).strip().replace(token, "<token>")


if not (REPO / ".git").exists():
    print("  init:", git(["init", "-b", "main"])[1].splitlines()[0])
    git(["config", "user.name", "Luis Chavarria Cayul"])
    git(["config", "user.email", "luisalbertochavarria@gmail.com"])

git(["add", "-A"])
code, out = git(["commit", "-m", "Portada del perfil profesional"])
print("  commit:", out.splitlines()[0] if out else code)

url = f"https://{login}:{token}@github.com/{login}/{login}.git"
code, out = git(["push", url, "main:main"])
print("  push:", "OK" if code == 0 else f"ERROR {out[:300]}")

# temas del repositorio
api("PUT", f"/repos/{login}/{login}/topics",
    {"names": ["perfil", "portafolio", "data", "analitica", "ia"]})

print("\n=== Contenido publicado ===")
c, archivos = api("GET", f"/repos/{login}/{login}/contents")
if isinstance(archivos, list):
    for a in archivos:
        print(f"  {a['name']}  ({a['size']:,} bytes)")
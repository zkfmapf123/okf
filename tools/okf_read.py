#!/usr/bin/env python3
"""okf_read.py — OKF 문서 읽기 도구.

게이트 동작이 아닌 일반 읽기에서, 로컬 ollama LLM 에 본문 요약을 위임할 수
있는 옵션을 제공한다. frontmatter 는 항상 raw 로 보존한다.

Usage:
  python okf_read.py --list-models
  python okf_read.py --read <path>
  python okf_read.py --read <path> --model <model>
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SUMMARIZE_PROMPT_KO = """다음은 OKF(YAML frontmatter + Markdown) 문서의 본문이다.
frontmatter 는 이미 제외된 상태이다.
헤딩 구조·표·코드블록·Citations 섹션은 그대로 유지하고,
서술 단락만 핵심을 잃지 않게 축약하여 한국어로 요약하라.

본문:
{body}
"""

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def ollama_available():
    return shutil.which("ollama") is not None


def list_models():
    if not ollama_available():
        return []
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []
    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return []
    models = []
    for line in lines[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def split_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def summarize_with_ollama(body, model):
    prompt = SUMMARIZE_PROMPT_KO.format(body=body)
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True, text=True, timeout=120, check=True,
    )
    return result.stdout.strip()


def cmd_list_models():
    return {
        "ollama_alive": ollama_available(),
        "available": list_models(),
    }


def cmd_read(path, model):
    p = Path(path).expanduser()
    if not p.exists():
        return {"error": f"file not found: {path}"}
    text = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    if not model or model == "default":
        return {
            "path": str(p),
            "frontmatter": fm,
            "body": body,
            "model_used": "default",
        }

    if not ollama_available():
        return {
            "path": str(p),
            "frontmatter": fm,
            "body": body,
            "model_used": "default",
            "warning": "ollama not installed; fell back to default",
        }

    try:
        summary = summarize_with_ollama(body, model)
    except subprocess.CalledProcessError as e:
        return {
            "path": str(p),
            "frontmatter": fm,
            "body": body,
            "model_used": "default",
            "warning": f"ollama call failed (exit {e.returncode}); fell back to default",
        }
    except subprocess.TimeoutExpired:
        return {
            "path": str(p),
            "frontmatter": fm,
            "body": body,
            "model_used": "default",
            "warning": "ollama call timed out; fell back to default",
        }

    return {
        "path": str(p),
        "frontmatter": fm,
        "body_summary": summary,
        "model_used": model,
    }


def main():
    parser = argparse.ArgumentParser(
        description="OKF document read tool with optional ollama delegation.",
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List available ollama models as JSON",
    )
    parser.add_argument(
        "--read", metavar="PATH",
        help="Path to OKF document to read",
    )
    parser.add_argument(
        "--model", default=None,
        help="Ollama model name; omit or use 'default' for raw read",
    )
    args = parser.parse_args()

    if args.list_models:
        print(json.dumps(cmd_list_models(), ensure_ascii=False, indent=2))
        return
    if args.read:
        out = cmd_read(args.read, args.model)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()

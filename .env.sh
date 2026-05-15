if [[ -f pyproject.toml ]]; then
  uv sync >/dev/null 2>&1
fi

if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate >/dev/null 2>&1
fi

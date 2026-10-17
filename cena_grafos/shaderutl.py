from __future__ import annotations

def readfile (filename: str) -> str:
  """Reads `filename` and returns its contents as a string; no path
  resolution or include-handling."""
  with open(filename, encoding="utf-8") as f:
    return f.read()


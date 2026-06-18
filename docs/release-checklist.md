# Release Checklist

PyPI publishing is manual until explicitly approved.

```powershell
git status --short
python -m pip install -e ".[dev]"
ruff check .
pytest

if (Test-Path .review-awep) { Remove-Item -Recurse -Force .review-awep }
awep fetch "https://example.com" --claim "Example Domain is used for illustrative examples" --agent-id release-check --tool-name smoke --storage-root .review-awep
awep report latest --storage-root .review-awep
awep verify latest --storage-root .review-awep

$p = Start-Process awep -ArgumentList 'serve','--port','8787','--storage-root','.review-awep' -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3
curl.exe -s http://127.0.0.1:8787/healthz
Stop-Process -Id $p.Id -Force

python -m pip install build twine
python -m build
python -m twine check dist/*
Get-ChildItem dist
```

Optional TestPyPI dry run:

```powershell
python -m twine upload --repository testpypi dist/*
```

Publish to PyPI only after manually approving the release artifacts:

```powershell
python -m twine upload dist/*
```

# PyPI Release Guide - UDS3 v1.4.0

Schritt-für-Schritt Anleitung zur Veröffentlichung auf PyPI.

## Voraussetzungen

### 1. PyPI Account erstellen
- Registriere dich auf https://pypi.org/account/register/
- Bestätige deine E-Mail-Adresse
- (Optional) Erstelle auch einen Account auf https://test.pypi.org/ zum Testen

### 2. API Token erstellen
1. Login auf PyPI: https://pypi.org/manage/account/
2. Gehe zu "Account settings" → "API tokens"
3. Klicke "Add API token"
4. Name: `uds3-upload`
5. Scope: "Entire account" (beim ersten Upload) oder "Project: uds3" (für Updates)
6. **WICHTIG:** Kopiere den Token sofort (wird nur einmal angezeigt!)
   - Format: `pypi-AgEIcHlwaS5vcmc...`

### 3. Token speichern
Erstelle/editiere `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Dein echter Token

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # TestPyPI Token (optional)
```

**Windows:** `C:\Users\<username>\.pypirc`  
**Linux/Mac:** `~/.pypirc`

**WICHTIG:** Setze Berechtigungen (nur du kannst lesen):
```powershell
# Windows PowerShell
icacls "$env:USERPROFILE\.pypirc" /inheritance:r /grant:r "$env:USERNAME:(R)"
```

## Build Process

### 1. Vorbereitung prüfen

```powershell
cd C:\VCC\uds3

# Prüfe Version in setup.py und pyproject.toml
# Beide sollten "1.4.0" zeigen

# Prüfe Git Status (alles sollte committed sein)
git status

# Prüfe README.md (wird als PyPI Beschreibung verwendet)
```

### 2. Package bauen

```powershell
# Alte Builds löschen
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Package bauen (Wheel + Source Distribution)
python -m build
```

**Erwartete Ausgabe:**
```
Successfully built uds3-1.4.0.tar.gz and uds3-1.4.0-py3-none-any.whl
```

**Dateien in `dist/`:**
- `uds3-1.4.0-py3-none-any.whl` - Wheel Package (Binary)
- `uds3-1.4.0.tar.gz` - Source Distribution

### 3. Package validieren

```powershell
# Prüfe Package-Inhalte
python -m tarfile -l dist/uds3-1.4.0.tar.gz

# Prüfe README-Rendering (wie es auf PyPI aussieht)
python -m twine check dist/*
```

**Erwartete Ausgabe:**
```
Checking dist/uds3-1.4.0-py3-none-any.whl: PASSED
Checking dist/uds3-1.4.0.tar.gz: PASSED
```

## Upload zu PyPI

### Option A: Test auf TestPyPI (EMPFOHLEN für ersten Upload)

```powershell
# Upload zu TestPyPI
python -m twine upload --repository testpypi dist/*

# Test-Installation
pip install --index-url https://test.pypi.org/simple/ --no-deps uds3==1.4.0
```

### Option B: Upload zu PyPI (Production)

```powershell
# Upload zu PyPI
python -m twine upload dist/*
```

**Interaktiver Prompt:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Enter your username: __token__
Enter your password: [API Token wird automatisch aus ~/.pypirc gelesen]

Uploading uds3-1.4.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 125.3/125.3 kB • 0:00:01
Uploading uds3-1.4.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 103.2/103.2 kB • 0:00:00

View at:
https://pypi.org/project/uds3/1.4.0/
```

## Nach dem Upload

### 1. Package-Seite prüfen
- Gehe zu: https://pypi.org/project/uds3/1.4.0/
- Prüfe:
  - ✅ README wird korrekt angezeigt
  - ✅ Version ist korrekt
  - ✅ Metadaten (Author, License, URLs) sind korrekt
  - ✅ Dependencies sind vollständig

### 2. Installation testen

```powershell
# Neue virtuelle Umgebung erstellen
python -m venv test_env
.\test_env\Scripts\Activate.ps1

# Package von PyPI installieren
pip install uds3==1.4.0

# Funktionalität testen
python -c "from uds3 import get_optimized_unified_strategy; print('✅ Import erfolgreich')"
python -m uds3 --version
python -m uds3 --health

# Aufräumen
deactivate
Remove-Item -Recurse test_env
```

### 3. Git Tag erstellen

```powershell
# Tag für Release erstellen
git tag -a v1.4.0 -m "Release v1.4.0: Enterprise PKI-Integrated Security Layer

- Row-Level Security (RLS)
- RBAC with 5 roles, 15 permissions
- PKI Certificate Authentication
- Audit Logging & Rate Limiting
- Secure Database API wrapper"

# Tag zu GitHub pushen
git push origin v1.4.0
```

### 4. GitHub Release erstellen
1. Gehe zu: https://github.com/makr-code/VCC-UDS3/releases/new
2. Tag: `v1.4.0`
3. Title: `UDS3 v1.4.0 - Enterprise Security Layer`
4. Beschreibung: Kopiere aus `docs/CHANGELOG.md` (v1.4.0 Sektion)
5. Füge Dateien hinzu:
   - `dist/uds3-1.4.0-py3-none-any.whl`
   - `dist/uds3-1.4.0.tar.gz`
6. ✅ "Create release"

## Troubleshooting

### Fehler: "File already exists"
```
HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
The name 'uds3' is already in use.
```

**Lösung:**
- PyPI erlaubt kein Überschreiben existierender Versionen
- Version in `setup.py` und `pyproject.toml` erhöhen (z.B. 1.4.1)
- Package neu bauen und uploaden

### Fehler: "Invalid credentials"
```
HTTPError: 403 Forbidden
Invalid or expired API token
```

**Lösung:**
- Prüfe `~/.pypirc` Token
- Erstelle neuen API Token auf PyPI
- Stelle sicher, dass Token mit `pypi-` beginnt

### Fehler: "README rendering failed"
```
The description failed to render for the following reason:
...
```

**Lösung:**
```powershell
# Prüfe README lokal
python -m twine check dist/*

# Häufige Probleme:
# - Ungültige Markdown-Syntax
# - Fehlende Bilder/Links
# - Nicht unterstützte Markdown-Features
```

### Fehler: "Missing dependencies"
```
error: package directory 'security' does not exist
```

**Lösung:**
- Prüfe `setup.py`: `find_packages()` findet alle Pakete
- Stelle sicher, dass alle Verzeichnisse `__init__.py` haben
- Prüfe `MANIFEST.in` für inkludierte Dateien

## Best Practices

### 1. Semantic Versioning
- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.4.x): Neue Features, backward-compatible
- **PATCH** (x.x.1): Bug fixes

### 2. Pre-Release Versions
Für Beta/RC Versionen:
```
1.4.0a1  # Alpha 1
1.4.0b2  # Beta 2
1.4.0rc3 # Release Candidate 3
```

### 3. Checklist vor Upload
- [ ] Alle Tests bestanden (`pytest`)
- [ ] Version erhöht (setup.py + pyproject.toml)
- [ ] CHANGELOG.md aktualisiert
- [ ] README.md aktualisiert
- [ ] Alle Änderungen committed
- [ ] Package gebaut (`python -m build`)
- [ ] Package validiert (`twine check`)
- [ ] TestPyPI Upload erfolgreich
- [ ] Installation von TestPyPI getestet

### 4. Automatisierung (CI/CD)
Für zukünftige Releases mit GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Zusammenfassung

```powershell
# Kompletter Release-Workflow
cd C:\VCC\uds3

# 1. Vorbereitung
git status  # Alles committed?
git pull    # Aktuell?

# 2. Build
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build

# 3. Validierung
python -m twine check dist/*

# 4. Upload (Test)
python -m twine upload --repository testpypi dist/*

# 5. Upload (Production)
python -m twine upload dist/*

# 6. Git Tag
git tag -a v1.4.0 -m "Release v1.4.0"
git push origin v1.4.0

# 7. GitHub Release erstellen (via Web UI)
```

## Support

- **PyPI Help:** https://pypi.org/help/
- **Packaging Guide:** https://packaging.python.org/
- **Twine Docs:** https://twine.readthedocs.io/

---

**Erstellt:** 24. Oktober 2025  
**Version:** 1.4.0  
**Autor:** UDS3 Team

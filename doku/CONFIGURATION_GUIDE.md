# UDS3 Configuration System Guide

## Overview

Das UDS3 Projekt verwendet ein mehrstufiges Konfigurationssystem, um zwischen Development/Stub-Umgebungen und produktiven Remote-Systemen zu unterscheiden.

## Configuration Files Structure

### 1. `config.py` (MAIN CONFIG - committed to Git)
- **Zweck**: Standard-Konfiguration für lokale Entwicklung und Stubs
- **Enthält**: Nur localhost-Verbindungen und Test-Credentials
- **Status**: ✅ Wird ins Git committed
- **Credentials**: Nur Stub-Passwörter wie "test"

### 2. `config_local.py` (LOCAL OVERRIDES - NOT committed)
- **Zweck**: Lokale Überschreibungen mit echten Remote-Verbindungen
- **Enthält**: Echte IP-Adressen, Benutzernamen und Passwörter
- **Status**: ❌ NICHT ins Git committed (in .gitignore)
- **Credentials**: Echte produktive Zugangsdaten

### 3. `database/config.py` (DATABASE SPECIFIC)
- **Zweck**: Detaillierte Database-Manager Konfiguration
- **Enthält**: Localhost/Stub-Konfigurationen für alle DB-Typen
- **Status**: ✅ Wird ins Git committed
- **Credentials**: Nur Stub-Passwörter

## How It Works

1. **Development Mode** (ohne config_local.py):
   ```python
   # Lädt nur config.py - alle Verbindungen zu localhost
   from uds3 import config
   print(config.DATABASES["graph"]["host"])  # → "localhost"
   ```

2. **Production Mode** (mit config_local.py):
   ```python
   # config.py lädt automatisch config_local.py wenn vorhanden
   # config_local.py überschreibt DATABASES, FEATURES, etc.
   from uds3 import config
   print(config.DATABASES["graph"]["host"])  # → "192.168.178.94"
   ```

## Configuration Values

### Default (Stub) Configuration
```python
DATABASES = {
    "postgis": {
        "host": "localhost",
        "user": "postgres", 
        "password": "test"  # Stub
    },
    "graph": {
        "host": "localhost",
        "user": "neo4j",
        "password": "test"  # Stub
    }
    # ... weitere localhost configs
}
```

### Production Override (config_local.py)
```python
DATABASES = {
    "postgis": {
        "host": "192.168.178.94",
        "user": "postgres",
        "password": "RealProductionPassword123"  # Real
    },
    "graph": {
        "host": "192.168.178.94", 
        "user": "neo4j",
        "password": "RealNeo4jPassword456"  # Real
    }
    # ... weitere remote configs
}
```

## Security Guidelines

### ✅ DO (Safe for Git)
- Localhost-Verbindungen in `config.py`
- Stub-Passwörter wie "test", "stub", "local"
- Debug-Features und Development-Flags
- Beispiel-Konfigurationen für Dokumentation

### ❌ DON'T (Never commit)
- Remote IP-Adressen in Standard-Configs
- Echte Passwörter oder API-Keys
- Produktive Datenbankverbindungen
- Interne Netzwerk-Informationen

## Setting Up Development Environment

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd uds3
   ```

2. **For Local Development** (uses stubs):
   ```python
   # Konfiguration wird automatisch geladen - nur localhost
   from uds3 import config
   # Funktioniert mit lokalen DBs oder Stubs
   ```

3. **For Production/Remote Access**:
   ```bash
   # Erstelle config_local.py (wird nicht committed!)
   cp config_local.py.example config_local.py
   # Editiere config_local.py mit echten Credentials
   ```

## File Status Check

```bash
# Diese Datei sollte NICHT in git status erscheinen:
git status | grep config_local.py  # Should return nothing

# Diese Dateien sind safe für Git:
git status | grep "config.py"      # Should show config.py changes
```

## Environment Variables Support

Beide Konfigurationssysteme unterstützen Environment Variables:

```bash
# Überschreibt auch config_local.py Werte
export POSTGRES_HOST="alternative-server.com"
export NEO4J_PASSWORD="env-based-password"
```

## Troubleshooting

### Problem: "Connection refused" zu localhost
```python
# Lösung: Erstelle config_local.py mit Remote-Servern
DATABASES = {
    "graph": {
        "host": "192.168.178.94",  # Remote server
        "password": "YourRealPassword"
    }
}
```

### Problem: config_local.py wird ins Git committed
```bash
# Lösung: Remove from git and add to gitignore
git rm --cached config_local.py
git commit -m "Remove config_local.py from git"
# File is already in .gitignore
```

### Problem: Falsche Konfiguration geladen
```python
# Debug: Prüfe welche Werte aktiv sind
from uds3 import config
print("Graph Host:", config.DATABASES["graph"]["host"])
print("Features:", config.FEATURES)
```

## Best Practices

1. **Nie echte Credentials in Standard-Configs**
2. **Immer config_local.py.example als Vorlage bereitstellen**
3. **Environment Variables für CI/CD verwenden** 
4. **Regelmäßig .gitignore Status prüfen**
5. **Dokumentation bei Config-Änderungen aktualisieren**

## Migration from Old Config

Falls alte Konfigurationen mit echten Credentials existieren:

```bash
# 1. Backup erstellen
cp config.py config_backup.py

# 2. Echte Credentials in config_local.py verschieben
# 3. config.py auf localhost/stubs umstellen
# 4. Git Status prüfen
git status | grep config
```
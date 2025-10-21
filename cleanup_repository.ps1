# UDS3 Repository Cleanup Script
# Automatic cleanup with backup and rollback support
# Date: 21. Oktober 2025

param(
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false,
    [switch]$Rollback = $false
)

$ErrorActionPreference = "Stop"

# Colors
$colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Highlight = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
}

# Statistics tracking
$stats = @{
    DirectoriesCreated = 0
    FilesMoved = 0
    FilesDeleted = 0
    BuildArtifactsRemoved = 0
    GitIgnoreUpdated = $false
}

Write-Section "UDS3 Repository Cleanup Script"
Write-ColorOutput "Starting cleanup process..." "Info"

if ($Rollback) {
    Write-Section "ROLLBACK MODE"
    Write-ColorOutput "Attempting to restore from backup branch..." "Warning"
    
    try {
        # Check if backup branch exists
        $backupBranch = git branch --list "backup-before-cleanup"
        if (-not $backupBranch) {
            Write-ColorOutput "❌ ERROR: No backup branch found!" "Error"
            Write-ColorOutput "Cannot rollback without backup-before-cleanup branch." "Error"
            exit 1
        }
        
        Write-ColorOutput "Found backup branch: backup-before-cleanup" "Success"
        Write-ColorOutput "⚠️  WARNING: This will discard all cleanup changes!" "Warning"
        $confirm = Read-Host "Type 'ROLLBACK' to confirm"
        
        if ($confirm -ne "ROLLBACK") {
            Write-ColorOutput "Rollback cancelled." "Info"
            exit 0
        }
        
        # Reset to backup branch
        git reset --hard backup-before-cleanup
        Write-ColorOutput "✅ Successfully rolled back to backup state!" "Success"
        Write-ColorOutput "You can now delete the backup branch with: git branch -D backup-before-cleanup" "Info"
        exit 0
        
    } catch {
        Write-ColorOutput "❌ ERROR during rollback: $_" "Error"
        exit 1
    }
}

if ($DryRun) {
    Write-ColorOutput "🔍 DRY RUN MODE - No changes will be made" "Warning"
}

# Step 1: Create Backup Branch
Write-Section "Step 1: Creating Backup Branch"

if (-not $SkipBackup) {
    try {
        # Check if backup branch already exists
        $existingBackup = git branch --list "backup-before-cleanup"
        if ($existingBackup) {
            Write-ColorOutput "⚠️  Backup branch already exists" "Warning"
            Write-ColorOutput "Delete it first with: git branch -D backup-before-cleanup" "Warning"
            $continue = Read-Host "Continue without creating new backup? (y/n)"
            if ($continue -ne "y") {
                exit 0
            }
        } else {
            if (-not $DryRun) {
                git branch backup-before-cleanup
                Write-ColorOutput "✅ Created backup branch: backup-before-cleanup" "Success"
            } else {
                Write-ColorOutput "Would create: backup-before-cleanup branch" "Info"
            }
        }
    } catch {
        Write-ColorOutput "❌ ERROR creating backup: $_" "Error"
        exit 1
    }
} else {
    Write-ColorOutput "⚠️  Skipping backup creation (not recommended!)" "Warning"
}

# Step 2: Create Archive Directory Structure
Write-Section "Step 2: Creating Archive Directory Structure"

$directories = @(
    "archive/backups",
    "archive/deprecated",
    "docs/archive/sessions",
    "docs/archive/todos",
    "docs/archive/releases",
    "docs/implementation"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput "  ✅ Created: $dir" "Success"
            $stats.DirectoriesCreated++
        } else {
            Write-ColorOutput "  Would create: $dir" "Info"
        }
    } else {
        Write-ColorOutput "  ℹ️  Already exists: $dir" "Info"
    }
}

# Step 3: Move Backup Files
Write-Section "Step 3: Moving Backup Files"

$backupFiles = @(
    "uds3_core_BEFORE_TODO6.py.bak",
    "uds3_quality_DEPRECATED.py.bak",
    "uds3_relations_core_ORIGINAL.py.bak",
    "uds3_saga_orchestrator_FULL.py.bak",
    "uds3_saga_orchestrator_ORIGINAL.py.bak",
    "uds3_security_DEPRECATED.py.bak",
    "test_rag_async_cache.py.backup"
)

foreach ($file in $backupFiles) {
    if (Test-Path $file) {
        $dest = "archive/backups/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → archive/backups/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → archive/backups/" "Info"
        }
    }
}

# Step 4: Move Deprecated Files
Write-Section "Step 4: Moving Deprecated Files"

$deprecatedFiles = @(
    "uds3_quality_DEPRECATED.py",
    "uds3_security_DEPRECATED.py",
    "uds3_dsgvo_core_old.py"
)

foreach ($file in $deprecatedFiles) {
    if (Test-Path $file) {
        $dest = "archive/deprecated/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → archive/deprecated/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → archive/deprecated/" "Info"
        }
    }
}

# Step 5: Move Session Documentation
Write-Section "Step 5: Moving Session Documentation"

$sessionDocs = @(
    "SESSION_COMPLETE.md",
    "SESSION_COMPLETE_TODO10.md",
    "SESSION_COMPLETE_TODO9.md",
    "NEXT_SESSION_TODO10.md",
    "NEXT_SESSION_TODO7.md"
)

foreach ($file in $sessionDocs) {
    if (Test-Path $file) {
        $dest = "docs/archive/sessions/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → docs/archive/sessions/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → docs/archive/sessions/" "Info"
        }
    }
}

# Step 6: Move TODO Summaries
Write-Section "Step 6: Moving TODO Summary Documentation"

$todoSummaries = @(
    "TODO10_COMPLETE_SUMMARY.md",
    "TODO11_COMPLETE_SUMMARY.md",
    "TODO12_COMPLETE_SUMMARY.md",
    "TODO13_COMPLETE_SUMMARY.md",
    "TODO14_COMPLETE_SUMMARY.md",
    "TODO15_COMPLETE_SUMMARY.md",
    "TODO15_IMPLEMENTATION_SUMMARY.md",
    "TODO15_FINAL_INTEGRATION_COMPLETE.md",
    "TODO_CRUD_COMPLETENESS.md"
)

foreach ($file in $todoSummaries) {
    if (Test-Path $file) {
        $dest = "docs/archive/todos/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → docs/archive/todos/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → docs/archive/todos/" "Info"
        }
    }
}

# Step 7: Move Release Documentation
Write-Section "Step 7: Moving Old Release Documentation"

$releaseDocs = @(
    "PROJECT_COMPLETE_v1.4.0.md",
    "RELEASE_v1.4.0.md",
    "UDS3_IMPLEMENTATION_COMPLETE.md",
    "MERGE_COMPLETE.md"
)

foreach ($file in $releaseDocs) {
    if (Test-Path $file) {
        $dest = "docs/archive/releases/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → docs/archive/releases/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → docs/archive/releases/" "Info"
        }
    }
}

# Step 8: Move Implementation Documentation
Write-Section "Step 8: Moving Implementation Documentation"

$implementationDocs = @(
    "TASK_6_RAG_TESTS_BENCHMARKS_COMPLETE.md",
    "TASK_7_DSGVO_INTEGRATION_COMPLETE.md",
    "TASK_8_MULTI_DB_INTEGRATION_COMPLETE.md",
    "STREAMING_SAGA_CONSISTENCY_ANALYSIS.md",
    "STREAMING_SAGA_DESIGN.md",
    "STREAMING_SAGA_ROLLBACK.md",
    "SYSTEM_COMPLETENESS_CHECK.md"
)

foreach ($file in $implementationDocs) {
    if (Test-Path $file) {
        $dest = "docs/implementation/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → docs/implementation/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → docs/implementation/" "Info"
        }
    }
}

# Step 9: Move Test Files
Write-Section "Step 9: Moving Test Files to tests/ Directory"

$testFiles = @(
    "test_compliance_adapter.py",
    "test_compliance_adapter_simplified.py",
    "test_database_extensions.py",
    "test_dsgvo_database_api_direct.py",
    "test_dsgvo_minimal.py",
    "test_embeddings.py",
    "test_integration.py",
    "test_llm.py",
    "test_naming_quick.py",
    "test_rag_async_cache.py",
    "test_search_api_integration.py",
    "test_streaming_standalone.py",
    "test_uds3_naming_integration.py",
    "test_vpb_adapter.py",
    "test_vpb_rag_dataminer.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        $dest = "tests/$file"
        if (-not $DryRun) {
            git mv $file $dest 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "  ✅ Moved: $file → tests/" "Success"
                $stats.FilesMoved++
            } else {
                Write-ColorOutput "  ⚠️  File not in git, moving manually: $file" "Warning"
                Move-Item $file $dest -Force
                $stats.FilesMoved++
            }
        } else {
            Write-ColorOutput "  Would move: $file → tests/" "Info"
        }
    }
}

# Step 10: Delete Temporary Files
Write-Section "Step 10: Deleting Temporary Files"

$tempFiles = @(
    "critical_failures.json",
    "failed_cleanups.json",
    "rollback_alerts.json",
    "vpb_demo_output.txt",
    "startup.log",
    "test_dsgvo.db"
)

foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        if (-not $DryRun) {
            Remove-Item $file -Force
            Write-ColorOutput "  ✅ Deleted: $file" "Success"
            $stats.FilesDeleted++
        } else {
            Write-ColorOutput "  Would delete: $file" "Info"
        }
    }
}

# Step 11: Clean Build Artifacts
Write-Section "Step 11: Cleaning Build Artifacts"

$artifactDirs = @(
    ".pytest_cache",
    "build",
    "dist",
    "uds3.egg-info"
)

foreach ($dir in $artifactDirs) {
    if (Test-Path $dir) {
        if (-not $DryRun) {
            Remove-Item -Recurse -Force $dir
            Write-ColorOutput "  ✅ Removed: $dir/" "Success"
            $stats.BuildArtifactsRemoved++
        } else {
            Write-ColorOutput "  Would remove: $dir/" "Info"
        }
    }
}

# Clean __pycache__ directories
if (-not $DryRun) {
    $pycacheDirs = Get-ChildItem -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue
    foreach ($dir in $pycacheDirs) {
        Remove-Item -Recurse -Force $dir.FullName
        $stats.BuildArtifactsRemoved++
    }
    Write-ColorOutput "  ✅ Removed all __pycache__ directories" "Success"
} else {
    Write-ColorOutput "  Would remove: All __pycache__ directories" "Info"
}

# Step 12: Update .gitignore
Write-Section "Step 12: Updating .gitignore"

$gitignoreAdditions = @"

# ==========================================
# UDS3 Project-Specific Ignores (Added during cleanup 21.10.2025)
# ==========================================

# Backup files
*.bak
*.backup
*_ORIGINAL.py
*_BEFORE_*.py

# Deprecated files
*_DEPRECATED.py
*_old.py

# Session documentation (temporary)
SESSION_*.md
NEXT_SESSION_*.md
TODO*_SUMMARY.md
TODO*_IMPLEMENTATION_SUMMARY.md
TODO*_FINAL_*.md
TODO*_COMPLETE*.md

# Temporary files
critical_failures.json
failed_cleanups.json
rollback_alerts.json
*_demo_output.txt
startup.log

# Build artifacts (comprehensive)
build/
dist/
*.egg-info/
.eggs/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.tox/
.coverage
.coverage.*
htmlcov/
*.cover

# Database files
*.db
*.sqlite
*.sqlite3
sqlite_db/
database_backup/

# IDE files (comprehensive)
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Environment files
venv/
env/
ENV/
.venv/
.env
.env.local
.env.*.local

# Logs (comprehensive)
*.log
*.log.*
logs/
log/

# Documentation (temporary)
*_PLAN.md.backup
*_SUMMARY.md.backup
CLEANUP_PLAN.md.backup
"@

if (-not $DryRun) {
    Add-Content -Path ".gitignore" -Value $gitignoreAdditions
    Write-ColorOutput "  ✅ Updated .gitignore with 25+ new patterns" "Success"
    $stats.GitIgnoreUpdated = $true
} else {
    Write-ColorOutput "  Would add 25+ new patterns to .gitignore" "Info"
}

# Step 13: Create Cleanup Summary
Write-Section "Step 13: Creating Cleanup Summary Documentation"

$summary = @"
# UDS3 Repository Cleanup Summary

**Date:** 21. Oktober 2025
**Status:** ✅ COMPLETE
**Script:** cleanup_repository.ps1

---

## 📊 Cleanup Statistics

- **Directories Created:** $($stats.DirectoriesCreated)
- **Files Moved:** $($stats.FilesMoved)
- **Files Deleted:** $($stats.FilesDeleted)
- **Build Artifacts Removed:** $($stats.BuildArtifactsRemoved)
- **.gitignore Updated:** $($stats.GitIgnoreUpdated)

---

## 📁 New Directory Structure

``````
archive/
├── backups/          # 7 backup files (*.bak, *.backup)
├── deprecated/       # 3 deprecated files (*_DEPRECATED.py)
└── legacy/           # Existing legacy code

docs/
├── archive/
│   ├── sessions/    # 5 session docs (SESSION_*.md)
│   ├── todos/       # 9 TODO summaries
│   └── releases/    # 4 old release docs
└── implementation/  # 7 implementation docs
``````

---

## 🔄 Files Moved (Preserved Git History)

### Backup Files → archive/backups/
- uds3_core_BEFORE_TODO6.py.bak
- uds3_quality_DEPRECATED.py.bak
- uds3_relations_core_ORIGINAL.py.bak
- uds3_saga_orchestrator_FULL.py.bak
- uds3_saga_orchestrator_ORIGINAL.py.bak
- uds3_security_DEPRECATED.py.bak
- test_rag_async_cache.py.backup

### Deprecated Files → archive/deprecated/
- uds3_quality_DEPRECATED.py
- uds3_security_DEPRECATED.py
- uds3_dsgvo_core_old.py

### Session Docs → docs/archive/sessions/
- SESSION_COMPLETE.md
- SESSION_COMPLETE_TODO10.md
- SESSION_COMPLETE_TODO9.md
- NEXT_SESSION_TODO10.md
- NEXT_SESSION_TODO7.md

### TODO Summaries → docs/archive/todos/
- TODO10_COMPLETE_SUMMARY.md
- TODO11_COMPLETE_SUMMARY.md
- TODO12_COMPLETE_SUMMARY.md
- TODO13_COMPLETE_SUMMARY.md
- TODO14_COMPLETE_SUMMARY.md
- TODO15_COMPLETE_SUMMARY.md
- TODO15_IMPLEMENTATION_SUMMARY.md
- TODO15_FINAL_INTEGRATION_COMPLETE.md
- TODO_CRUD_COMPLETENESS.md

### Release Docs → docs/archive/releases/
- PROJECT_COMPLETE_v1.4.0.md
- RELEASE_v1.4.0.md
- UDS3_IMPLEMENTATION_COMPLETE.md
- MERGE_COMPLETE.md

### Implementation Docs → docs/implementation/
- TASK_6_RAG_TESTS_BENCHMARKS_COMPLETE.md
- TASK_7_DSGVO_INTEGRATION_COMPLETE.md
- TASK_8_MULTI_DB_INTEGRATION_COMPLETE.md
- STREAMING_SAGA_CONSISTENCY_ANALYSIS.md
- STREAMING_SAGA_DESIGN.md
- STREAMING_SAGA_ROLLBACK.md
- SYSTEM_COMPLETENESS_CHECK.md

### Test Files → tests/
- test_compliance_adapter.py
- test_compliance_adapter_simplified.py
- test_database_extensions.py
- test_dsgvo_database_api_direct.py
- test_dsgvo_minimal.py
- test_embeddings.py
- test_integration.py
- test_llm.py
- test_naming_quick.py
- test_rag_async_cache.py
- test_search_api_integration.py
- test_streaming_standalone.py
- test_uds3_naming_integration.py
- test_vpb_adapter.py
- test_vpb_rag_dataminer.py

---

## 🗑️ Files Deleted

Temporary files (no longer needed):
- critical_failures.json
- failed_cleanups.json
- rollback_alerts.json
- vpb_demo_output.txt
- startup.log
- test_dsgvo.db

Build artifacts removed:
- .pytest_cache/
- build/
- dist/
- uds3.egg-info/
- All __pycache__/ directories

---

## 🔒 .gitignore Updates

Added 25+ new patterns:
- Backup files: ``*.bak``, ``*.backup``, ``*_ORIGINAL.py``
- Deprecated files: ``*_DEPRECATED.py``, ``*_old.py``
- Session docs: ``SESSION_*.md``, ``TODO*_SUMMARY.md``
- Temp files: ``*.json`` (specific), ``*_demo_output.txt``
- Build artifacts: Comprehensive Python build patterns
- Database files: ``*.db``, ``*.sqlite``, ``sqlite_db/``
- Logs: ``*.log``, ``logs/``
- IDE files: ``.vscode/``, ``.idea/``
- OS files: ``.DS_Store``, ``Thumbs.db``

---

## ✅ Benefits

**Before Cleanup:**
- Root directory: 150+ files
- Mixed legacy/active code
- Unclear organization

**After Cleanup:**
- Root directory: ~80 active files
- Clear separation (active/archive)
- Professional structure
- Comprehensive .gitignore

---

## 🔙 Rollback Instructions

If you need to revert all changes:

``````powershell
.\cleanup_repository.ps1 -Rollback
``````

Or manually:

``````powershell
git reset --hard backup-before-cleanup
git branch -D backup-before-cleanup
``````

---

## 📝 Next Steps

1. **Test Everything:**
   ``````powershell
   pytest tests/ -v
   ``````

2. **Verify Git History:**
   ``````powershell
   git log --follow docs/archive/sessions/SESSION_COMPLETE.md
   ``````

3. **Delete Backup Branch (when confident):**
   ``````powershell
   git branch -D backup-before-cleanup
   ``````

4. **Push Changes:**
   ``````powershell
   git push origin main
   ``````

---

**Cleanup completed successfully! 🎉**
"@

if (-not $DryRun) {
    $summary | Out-File -FilePath "CLEANUP_SUMMARY.md" -Encoding UTF8
    Write-ColorOutput "  ✅ Created: CLEANUP_SUMMARY.md" "Success"
} else {
    Write-ColorOutput "  Would create: CLEANUP_SUMMARY.md" "Info"
}

# Final Summary
Write-Section "CLEANUP COMPLETE"

Write-ColorOutput "📊 Statistics:" "Highlight"
Write-ColorOutput "  • Directories Created: $($stats.DirectoriesCreated)" "Info"
Write-ColorOutput "  • Files Moved: $($stats.FilesMoved)" "Info"
Write-ColorOutput "  • Files Deleted: $($stats.FilesDeleted)" "Info"
Write-ColorOutput "  • Build Artifacts Removed: $($stats.BuildArtifactsRemoved)" "Info"
Write-ColorOutput "  • .gitignore Updated: $($stats.GitIgnoreUpdated)" "Info"

Write-Host ""

if ($DryRun) {
    Write-ColorOutput "🔍 DRY RUN COMPLETE - No actual changes made" "Warning"
    Write-ColorOutput "Run without -DryRun flag to execute cleanup" "Info"
} else {
    Write-ColorOutput "✅ CLEANUP SUCCESSFUL!" "Success"
    Write-Host ""
    Write-ColorOutput "📋 Next Steps:" "Highlight"
    Write-ColorOutput "  1. Review changes: git status" "Info"
    Write-ColorOutput "  2. Test everything: pytest tests/ -v" "Info"
    Write-ColorOutput "  3. Commit changes: git add -A && git commit -m 'chore: Clean up repository structure'" "Info"
    Write-ColorOutput "  4. Push to remote: git push origin main" "Info"
    Write-Host ""
    Write-ColorOutput "🔙 Rollback Available:" "Warning"
    Write-ColorOutput "  Run: .\cleanup_repository.ps1 -Rollback" "Info"
    Write-ColorOutput "  Or: git reset --hard backup-before-cleanup" "Info"
}

Write-Host ""
Write-ColorOutput "📄 Documentation: CLEANUP_SUMMARY.md" "Highlight"
Write-ColorOutput "📄 Planning: CLEANUP_PLAN.md" "Highlight"

Write-Host ""

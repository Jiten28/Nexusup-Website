<#
 NexusUp database helper for Windows (PowerShell 5.1 or 7).   Usage:  .\db.ps1 <command> [argument]
 Needs Docker Desktop (running). Reads database\.env. Your SQLite file is only ever read.
 If scripts are blocked:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>
param([Parameter(Position=0)][string]$Command = 'help', [Parameter(Position=1)][string]$Arg = '')
$ErrorActionPreference = 'Stop'
$DbDir   = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path (Split-Path -Parent $DbDir) 'backend'
Set-Location $DbDir
if (-not (Test-Path .env)) { throw 'Missing database\.env - run: Copy-Item database\.env.example database\.env  and set the passwords.' }
$cfg = @{}
Get-Content .env | Where-Object { $_ -match '^\s*[^#\s][^=]*=' } | ForEach-Object { $k, $v = $_ -split '=', 2; $cfg[$k.Trim()] = $v.Trim() }
if (-not $cfg.DB_PORT) { $cfg.DB_PORT = '3306' }
$Py = Join-Path $Backend '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { $Py = 'python' }

function DC { docker compose --env-file .env -f compose.yaml @args; if ($LASTEXITCODE) { throw "docker compose failed ($LASTEXITCODE)" } }
function Wait-Ready {
  Write-Host -NoNewline 'Waiting for MariaDB'
  for ($i = 0; $i -lt 60; $i++) {
    $s = docker inspect -f '{{.State.Health.Status}}' nexusup-db 2>$null
    if ($s -eq 'healthy') { Write-Host ' ready.'; return }
    Write-Host -NoNewline '.'; Start-Sleep 2
  }
  throw 'MariaDB did not become healthy. Check: docker compose logs db'
}
function Use-MariaDb {   # environment the Django backend needs for this MariaDB
  $env:DB_ENGINE = 'mariadb'; $env:DB_NAME = $cfg.DB_NAME; $env:DB_USER = $cfg.DB_USER
  $env:DB_PASSWORD = $cfg.DB_PASSWORD; $env:DB_HOST = '127.0.0.1'; $env:DB_PORT = $cfg.DB_PORT; $env:DJANGO_DEBUG = '1'
}
function Manage { Push-Location $Backend; try { & $Py manage.py @args; if ($LASTEXITCODE) { throw "manage.py $($args -join ' ') failed" } } finally { Pop-Location } }

switch ($Command) {
  'up'     { DC up -d db; Wait-Ready }
  'down'   { DC stop db; Write-Host 'Stopped. Your data is kept in the Docker volume.' }
  'status' { DC ps; Use-MariaDb; Manage shell -c "from django.db import connection as c; c.ensure_connection(); print('Django connected to', c.vendor, c.settings_dict['NAME'], 'on', c.settings_dict['HOST'])" }
  'create' { DC up -d db; Wait-Ready; Use-MariaDb; Manage migrate }
  'export' {
    $out = if ($Arg) { $Arg } else { Join-Path $DbDir ("backups\nexusup-{0}.sql" -f (Get-Date -Format 'yyyyMMdd-HHmmss')) }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
    DC exec -T db sh /scripts/export.sh
    docker cp nexusup-db:/tmp/export.sql $out; Write-Host "Exported to $out"
  }
  'import' {
    if (-not $Arg -or -not (Test-Path $Arg)) { throw 'Usage: .\db.ps1 import path\to\file.sql' }
    Read-Host "This will overwrite tables in database '$($cfg.DB_NAME)'. Press Enter to continue, Ctrl+C to cancel" | Out-Null
    DC up -d db; Wait-Ready
    docker cp (Resolve-Path $Arg) nexusup-db:/tmp/import.sql
    DC exec -T db sh /scripts/import.sh
    Write-Host "Imported $Arg"
  }
  'from-sqlite' {
    $sqlite = if ($Arg) { $Arg } else { Join-Path $Backend 'demo.sqlite3' }
    if (-not (Test-Path $sqlite)) { throw "SQLite file not found: $sqlite" }
    $sqlite = (Resolve-Path $sqlite).Path
    New-Item -ItemType Directory -Force -Path (Join-Path $DbDir 'backups') | Out-Null
    $dump = Join-Path $DbDir ("backups\sqlite-data-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Write-Host "Reading (read-only) $sqlite"
    $env:DB_ENGINE = 'sqlite'; $env:DJANGO_DEBUG = '1'; $env:SQLITE_PATH = $sqlite
    Manage dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --exclude admin.logentry --indent 1 --output $dump
    Remove-Item Env:SQLITE_PATH
    DC up -d db; Wait-Ready; Use-MariaDb
    Manage migrate
    Push-Location $Backend
    try {
      & $Py manage.py shell -c "import sys; from apps.news.models import Article; sys.exit(1 if Article.objects.exists() else 0)"
      if ($LASTEXITCODE) { throw "MariaDB already contains articles - refusing to import on top of them. Run '.\db.ps1 export' first, or use '.\db.ps1 reset'." }
    } finally { Pop-Location }
    Manage loaddata $dump
    Write-Host "Done. Intermediate file kept at $dump (delete it when you are happy)."
  }
  'reset'  { if ((Read-Host 'This DELETES the MariaDB volume and all its data. Type RESET to continue') -eq 'RESET') { DC down -v; Write-Host 'Volume removed.' } }
  default  {
@'
Commands:
  up                start MariaDB in Docker
  create            create all tables (Django migrate)
  status            show container state and test the Django connection
  export [file]     save the whole database to database\backups\*.sql
  import <file>     restore a .sql file
  from-sqlite [db]  copy your existing SQLite data into an empty MariaDB (SQLite is only read)
  down              stop MariaDB (data is kept)
  reset             delete the MariaDB volume (asks for confirmation)
'@ | Write-Host
  }
}

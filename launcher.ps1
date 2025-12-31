# launcher.ps1 - Updated for src\writer_v3.py
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile = "C:\AI_Projects\AI_Newsletter\scheduler_debug.log"
$projectDir = "C:\AI_Projects\AI_Newsletter"

# --- CONFIGURATION ---
# Pointing to the file inside the 'src' folder
$scriptFile = "src\writer_v3.py"
$pythonExe  = "$projectDir\.venv\Scripts\python.exe"
# ---------------------

# 1. Clear previous log to prevent encoding errors
Clear-Content -Path $logFile -ErrorAction SilentlyContinue

# 2. Start Logging
"------------------------------------------------" | Out-File -FilePath $logFile -Encoding ascii
"[$date] START: Attempting to launch pipeline..." | Out-File -FilePath $logFile -Append -Encoding ascii

# 3. Force Working Directory (Keep this at Root so 'data/' imports work)
Set-Location -Path $projectDir
"[$date] INFO: Working directory set to: $projectDir" | Out-File -FilePath $logFile -Append -Encoding ascii
"[$date] INFO: Target Script: $scriptFile" | Out-File -FilePath $logFile -Append -Encoding ascii

# 4. Check if Python exists
if (-Not (Test-Path $pythonExe)) {
    "[$date] ERROR: Python executable not found at $pythonExe" | Out-File -FilePath $logFile -Append -Encoding ascii
    Exit 1
}

# 5. Check if Script exists
if (-Not (Test-Path $scriptFile)) {
    "[$date] ERROR: Script file not found: $scriptFile" | Out-File -FilePath $logFile -Append -Encoding ascii
    Exit 1
}

# 6. Execute
try {
    # We execute from the root, calling the script in src
    & $pythonExe $scriptFile | Out-File -FilePath $logFile -Append -Encoding ascii
    "[$date] END: Script execution finished." | Out-File -FilePath $logFile -Append -Encoding ascii
}
catch {
    $errorMessage = $_.Exception.Message
    "[$date] CRITICAL FAILURE: $errorMessage" | Out-File -FilePath $logFile -Append -Encoding ascii
}
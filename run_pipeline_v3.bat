# --- Bapi's AI Pipeline Wrapper (V3.4) ---
$projectRoot = "C:\AI_Projects\AI_Newsletter"
$pythonPath = "$projectRoot\.venv\Scripts\python.exe"
$logFile = "$projectRoot\pipeline_log.txt"

# Helper Function to Log
function Log-Message {
    param ([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $msg" | Out-File -FilePath $logFile -Append
    Write-Host "$timestamp $msg"
}

# Helper Function to Run Script
function Run-Script {
    param ([string]$scriptName)
    Log-Message "START: Running $scriptName..."
    
    # Run Python and capture output
    $process = Start-Process -FilePath $pythonPath -ArgumentList "src\$scriptName" -RedirectStandardOutput "$projectRoot\temp_out.txt" -RedirectStandardError "$projectRoot\temp_err.txt" -PassThru -Wait -WindowStyle Hidden
    
    # Append Output to Main Log
    if (Test-Path "$projectRoot\temp_out.txt") { Get-Content "$projectRoot\temp_out.txt" | Out-File -FilePath $logFile -Append }
    if (Test-Path "$projectRoot\temp_err.txt") { Get-Content "$projectRoot\temp_err.txt" | Out-File -FilePath $logFile -Append }

    if ($process.ExitCode -eq 0) {
        Log-Message "SUCCESS: $scriptName finished."
    } else {
        Log-Message "ERROR: $scriptName failed with Exit Code $($process.ExitCode)."
    }
}

# --- MAIN EXECUTION FLOW ---
Log-Message "========================================"
Log-Message "PIPELINE STARTED (SYSTEM ACCOUNT)"

Set-Location -Path $projectRoot

# 1. FETCH
Run-Script "fetcher_v3.py"

# 2. PROCESS (Cluster)
Run-Script "ai_processor_v3.py"

# 3. WRITE (Ollama)
Run-Script "writer_v3.py"

# 4. EMAIL
Run-Script "emailer_v3.py"

Log-Message "PIPELINE COMPLETED"
Log-Message "========================================"
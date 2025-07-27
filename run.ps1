# Define the base path relative to this script
$basePath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Define agent configurations: folder name, port, and ID
$agents = @(
    @{ Name = "ComprehensiveReceiptAgent"; Port = 8084; Id = 101 },
    @{ Name = "CSAgent"; Port = 8082; Id = 102 },
    @{ Name = "SmartFinancialAdvisorAgent"; Port = 8083; Id = 103 }
    @{ Name = "risk_analyzer_agent"; Port = 8085; Id = 104 }
    @{ Name = "investment_planner_agent"; Port = 8086; Id = 105 }
    @{ Name = "FiMoneyAgent"; Port = 8090; Id = 106 }
)

# Start each agent in a new PowerShell window
foreach ($agent in $agents) {
    $agentPath = Join-Path -Path $basePath -ChildPath "agents\$($agent.Name)"
    $port = $agent.Port
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$agentPath`"; uv run __main__.py --host localhost --port $port"
}

# Start host agent on port 8080
$hostPath = Join-Path -Path $basePath -ChildPath "host_agent"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$hostPath`"; uv run __main__.py --host localhost --port 8080"

# Wait for all services to start
Start-Sleep -Seconds 50

# Health check for host agent using status code
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Host agent is running (status code: 200)."
    } else {
        Write-Error "❌ Host agent health check failed with status code $($response.StatusCode)."
        exit 1
    }
} catch {
    Write-Error "❌ Host agent is not reachable. Exception: $($_.Exception.Message)"
    exit 1
}

# Register each agent to the host agent
foreach ($agent in $agents) {
    $payload = @{
        id      = "$($agent.Id)"
        jsonrpc = "2.0"
        method  = "agent/register"
        params  = "localhost:$($agent.Port)"
    } | ConvertTo-Json -Compress

    try {
        $registerResponse = Invoke-RestMethod -Uri "http://localhost:8080/agent/register" -Method POST -Body $payload -ContentType "application/json"
        Write-Host "✅ Registered agent '$($agent.Name)' on port $($agent.Port)"
    } catch {
        Write-Warning "⚠️ Failed to register agent '$($agent.Name)' on port $($agent.Port): $($_.Exception.Message)"
    }
}


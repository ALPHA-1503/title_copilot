$mistral_port = 22028
$mistral_remote_port = 22002

$ssh_mistral = "ssh -N -f -p $mistral_remote_port user@idaho-b.tensordockmarketplace.com -i ~\.ssh\id_rsa_tensordock -L 22028:localhost:8000 2> $null"

function exec_ssh($SSH_COMMAND) {
    Start-Process -FilePath "powershell" -ArgumentList "-Command", $SSH_COMMAND -NoNewWindow
}

function message($port){
    Write-Host "[SSH TUNNEL] " -ForegroundColor Green -NoNewline
    Write-Host "Port $port is open on localhost"
}

# Check if local mistral port is open (listening)
$mistral_PORT_STATUS = netstat -an | Select-String -Pattern ":$mistral_port.*LISTENING"
if (-not $mistral_PORT_STATUS) {
    Write-Host "Port $mistral_port is closed on localhost. Running SSH command..."
    exec_ssh $ssh_mistral
}

# Verify remote connection
$mistral_STATUS = Get-NetTCPConnection -State Established -RemotePort $mistral_remote_port 2> $null

if ($mistral_STATUS) {
    message($mistral_port)
    python .\scripts\before_code.py
    python .\App.py
} else {
    Write-Host "Execution of SSH tunnel was unsuccessful." -ForegroundColor Red
    Write-Host "`nPlease check the Remote Virtual Machine. It must be running to use the APP!" -ForegroundColor Yellow
    Write-Host "Follow these instructions for the deployment of the cloud GPU via TensorDock." -ForegroundColor Yellow
    Write-Host "https://gitlab.sw.goiba.net/req-test-tools/polarion-copilot/copilot-proto#polarioncopilot`n" -ForegroundColor Blue
}
# Execute na mesma janela PowerShell em que executara o Terraform.
$tokenSeguro = Read-Host 'Token pessoal Aiven (entrada oculta)' -AsSecureString
try {
    $env:AIVEN_TOKEN = [System.Net.NetworkCredential]::new('', $tokenSeguro).Password
} finally {
    $tokenSeguro.Dispose()
}
Write-Output 'AIVEN_TOKEN configurado apenas neste processo. Nao foi salvo em arquivo.'

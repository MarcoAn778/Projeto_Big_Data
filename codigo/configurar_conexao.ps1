# Execute na raiz do repositorio, na mesma janela que executara Rscript.
$env:PGHOST = Read-Host 'Host PostgreSQL mostrado no Aiven'
$env:PGPORT = Read-Host 'Porta PostgreSQL mostrada no Aiven'
$env:PGDATABASE = Read-Host 'Banco de dados (normalmente defaultdb)'
$env:PGUSER = Read-Host 'Usuario PostgreSQL mostrado no Aiven'
$caLocal = Read-Host 'Caminho completo do certificado CA baixado do Aiven'
if (-not (Test-Path -LiteralPath $caLocal -PathType Leaf)) { throw 'Certificado CA nao encontrado' }
$env:PGSSLROOTCERT = (Resolve-Path -LiteralPath $caLocal).Path
$senhaSegura = Read-Host 'Senha PostgreSQL (entrada oculta)' -AsSecureString
try {
    $env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $senhaSegura).Password
} finally {
    $senhaSegura.Dispose()
}
Write-Output 'Conexao configurada apenas nesta janela. Agora execute Rscript codigo/executar.R carga.'

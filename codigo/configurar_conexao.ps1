# Execute na raiz do repositorio, na mesma janela que executara Python.
$env:PGHOST = Read-Host 'Host PostgreSQL do provedor'
$env:PGPORT = Read-Host 'Porta PostgreSQL'
$env:PGDATABASE = Read-Host 'Nome do banco de dados'
$env:PGUSER = Read-Host 'Usuario PostgreSQL'
$caLocal = Read-Host 'Caminho completo do certificado CA do provedor'
if (-not (Test-Path -LiteralPath $caLocal -PathType Leaf)) { throw 'Certificado CA nao encontrado' }
$env:PGSSLROOTCERT = (Resolve-Path -LiteralPath $caLocal).Path
$senhaSegura = Read-Host 'Senha PostgreSQL (entrada oculta)' -AsSecureString
try {
    $env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $senhaSegura).Password
} finally {
    $senhaSegura.Dispose()
}
Write-Output 'Conexao configurada nesta janela. Verifique com python codigo/diagnosticar_conexao.py.'

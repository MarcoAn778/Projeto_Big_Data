# Concluir a implantação e a entrega

Se o projeto já tem um serviço Aiven, consulte primeiro a seção de reaproveitamento e conciliação do [guia do painel](DASHBOARD.md).

O fluxo desta revisão é **R trata → CSV tratado → Python valida e carrega → PostgreSQL/Aiven**, com a infraestrutura criada pelo Terraform. Todos os arquivos da entrega anterior estão preservados. As instruções atuais estão em `LEIA_ME_ETAPA_ATUAL.md`, separado do README original. Esta preparação é local; a equipe decide quando publicar. A criação do banco exige sua conta no Aiven. Nenhuma senha ou token deve ser enviado pelo chat ou publicado no GitHub.

## 1. Preparar a máquina e validar a base

1. Extraia o pacote `PROJETO_BIG_DATA_MARCO2_PYTHON.zip` e abra a pasta `Projeto_Big_Data`.
2. Instale [Python](https://www.python.org/downloads/windows/) 64 bits (3.12 é a versão testada) e [Terraform](https://developer.hashicorp.com/terraform/install). R só será necessário se decidir refazer o tratamento dos TXT.
3. Abra um PowerShell nessa pasta. Todos os comandos seguintes partem da pasta que contém `README.md`, `codigo/` e `infraestrutura/`.
4. Crie o ambiente Python e instale as versões verificadas:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe codigo/executar.py validar
.\.venv\Scripts\python.exe -m unittest discover -s testes -p "test_*.py" -v
```

Não é necessário ativar a venv. Se o launcher `py` não estiver disponível, use `python -m venv .venv` após conferir a versão instalada. Para outras versões compatíveis de Python, também existe `requirements.txt`; o lock registra as versões usadas nesta validação.

O resultado esperado da validação é **1.006.405 linhas, 51.893.337 movimentações e 12 meses**. Ela extrai o ZIP da base quando necessário e escreve `verificacoes/validacao_base_atual.json`. Os dez testes locais devem passar; dois testes de integração ficam ignorados sem um banco local descartável configurado. Eles já foram executados na preparação desta revisão, como descrito no registro de validação.

Não é necessário copiar os TXT ou executar R novamente para carregar a base publicada. Para reproduzir o tratamento integral, instale no R `DBI`, `duckdb`, `digest` e `jsonlite`, coloque os 12 TXT em `dados_originais/` e execute `Rscript codigo/executar.R tratamento`. Depois retorne à validação em Python.

## 2. Criar a conta e o projeto Aiven

1. Acesse [Aiven Console](https://console.aiven.io/) e crie a conta da equipe, concluindo a verificação de e-mail.
2. Identifique ou crie um projeto e anote seu nome exato.
3. Gere um token pessoal nas configurações de autenticação da conta, com prazo e permissões adequados ao projeto. Consulte o [passo a passo oficial](https://aiven.io/docs/platform/howto/create_authentication_token).
4. Não crie o serviço manualmente: o próximo passo cria o PostgreSQL por Terraform.

O plano padrão do código é `free-1-1gb`. Confirme que ele está disponível para o projeto. Se a plataforma não disponibilizar o plano gratuito, interrompa a implantação e revise a escolha; o código bloqueia planos pagos. A existência de um serviço gratuito do mesmo tipo na organização pode impedir outro.

## 3. Configurar e aplicar o Terraform

Na raiz do repositório:

```powershell
Copy-Item infraestrutura/terraform.tfvars.example infraestrutura/terraform.tfvars
.\infraestrutura\configurar_token.ps1
```

Edite apenas a cópia local `infraestrutura/terraform.tfvars`:

- substitua `project_name` pelo nome real do projeto;
- mantenha `plan = "free-1-1gb"` se disponível;
- substitua `203.0.113.10/32` pelo IP público da sua rede seguido de `/32`;
- inclua os demais IPs necessários para a equipe, se aplicável.

O IP do exemplo é reservado para documentação e não permite acesso da sua máquina. Use o IP público da sua rede mostrado pelo roteador ou pela ferramenta de consulta de IP de sua preferência. O token é solicitado em entrada oculta pelo script, sem aparecer no histórico. Se o PowerShell bloquear scripts locais, confira o conteúdo dos dois `.ps1` e, para esta janela, ajuste a política de execução conforme a configuração da sua máquina; não é necessário alterar a política global.

Como esta pasta pode estar no OneDrive, guarde o estado Terraform fora dela. Os comandos abaixo criam o diretório privado de estado no perfil local da máquina:

```powershell
$estadoCaged = Join-Path $env:LOCALAPPDATA 'ProjetoBigData'
New-Item -ItemType Directory -Path $estadoCaged -Force | Out-Null
$arquivoEstadoCaged = (Join-Path $estadoCaged 'terraform.tfstate').Replace('\', '/')
terraform -chdir=infraestrutura init -backend-config="path=$arquivoEstadoCaged"
terraform -chdir=infraestrutura fmt -check -recursive
terraform -chdir=infraestrutura validate
terraform -chdir=infraestrutura test
terraform -chdir=infraestrutura plan
terraform -chdir=infraestrutura apply
```

Leia o plano antes de confirmar o `apply`: deve criar um serviço PostgreSQL no projeto correto, no plano gratuito, sem exclusões. Aguarde o serviço ficar disponível. Preserve o mesmo state em execuções futuras e mantenha uma cópia privada segura. O lock `.terraform.lock.hcl` deve ser versionado; `terraform.tfvars`, state e planos não devem ser publicados. Não use `terraform output -json` ou exportação do state como evidência pública.

Se um banco já tiver sido criado manualmente antes de seguir este guia, configure o nome e parâmetros correspondentes e importe-o primeiro:

```powershell
terraform -chdir=infraestrutura import aiven_pg.caged PROJETO/SERVICO
terraform -chdir=infraestrutura plan
```

Importar um recurso existente não prova que ele foi originalmente provisionado por Terraform. Registre essa distinção na entrega caso esse caminho seja utilizado.

## 4. Configurar a conexão e carregar

No painel do serviço, obtenha host, porta, banco, usuário e senha e baixe a CA. Mantenha o arquivo CA em local privado. É possível usar `segredos/ca.pem`, ignorado pelo Git; o certificado CA serve para verificar o servidor e não substitui a senha.

Na mesma janela PowerShell em que executará Python:

```powershell
.\codigo\configurar_conexao.ps1
.\.venv\Scripts\python.exe codigo/executar.py carga
.\.venv\Scripts\python.exe codigo/executar.py verificar-nuvem
```

Informe os valores do painel nos prompts. O banco geralmente é `defaultdb`, mas use o valor realmente informado pelo serviço. A senha será solicitada com entrada oculta. Se a conexão falhar, confira o IP público autorizado, a porta e a CA. Não desative a validação de certificado.

A carga usa uma transação e transmite os CSVs em blocos de bytes por `COPY`, preservando os valores decimais. Ela confere totais, contagens mensais e soma salarial antes do commit. Se houver erro antes dele, as alterações da carga são revertidas. Após o commit, há nova conferência e geração da evidência. Se o schema já tiver dados, a carga para para evitar duplicação; para conferir uma carga existente, use `verificar-nuvem`. Nenhuma tabela é apagada automaticamente. O modo de verificação não altera o banco.

## 5. Guardar evidências e atualizar o status

Após uma execução real bem-sucedida:

1. Confirme `verificacoes/carga_nuvem.json` com status `carga_nuvem_validada` e os totais da base.
2. No Aiven, confira o serviço disponível, plano e uso de disco. Não confunda o tamanho do CSV com o tamanho do banco, índices e espaço de operação. O plano gratuito tem capacidade limitada.
3. Guarde uma evidência do `apply` concluído, com data e quantidade de recursos criados, removendo dados de acesso. Uma captura deve ocultar senha, token e URI de conexão.
4. Execute [consultas_validacao.sql](../sql/consultas_validacao.sql) para apresentar resultados por mês e a auditoria.
5. Atualize o status no README e em `documentacao/ENTREGA.md` somente depois dessas verificações. Registre a data real do provisionamento e da carga.

A evidência gerada por Python contém totais, hash, confirmação de TLS, conferência salarial, tamanho do banco e data. Ela não contém host, usuário, senha ou token. `verificacoes/carga_python_teste_local.json` identifica somente o teste em PostgreSQL local e não substitui a evidência de nuvem `carga_nuvem.json`.

## 6. Publicar no GitHub e enviar

A publicação deve ser realizada manualmente pela equipe, após revisar os arquivos e concluir a implantação. Primeiro, gere o pacote limpo a partir da sua execução real:

```powershell
.\.venv\Scripts\python.exe codigo/preparar_envio.py
```

O comando bloqueia o envio final se não houver a evidência `carga_nuvem.json` da base atual. Ele grava `output/envio/PROJETO_BIG_DATA_ENVIO.zip` sem credenciais, ambiente virtual ou estado Terraform. Não envia arquivos à internet. Extraia **esse ZIP de envio em uma pasta nova** e abra a pasta `Projeto_Big_Data`. No repositório existente do GitHub, use **Add file → Upload files** para enviar o conteúdo dessa pasta limpa para a raiz, preservando os nomes e diretórios.

Adicione `LEIA_ME_ETAPA_ATUAL.md`, `.gitignore`, `.gitattributes`, `requirements.txt`, `requirements-lock.txt`, `infraestrutura/`, `documentacao/` e os arquivos novos nas demais pastas. Em `codigo/`, inclua `executar.py` e a pasta `caged/` com seus arquivos Python. Preserve todos os arquivos anteriores. A base compactada em `resultados/` e os dicionários em `referencias/` continuam nas suas pastas. Inclua o lock `.terraform.lock.hcl`; confirme que arquivos iniciados por ponto também foram selecionados no upload.

Preserve os arquivos da etapa anterior, inclusive os scripts R `00` a `05`: não é necessário remover ou editar nenhum deles para usar Python. Os comandos desta etapa usam os arquivos Python novos. `verificacoes/preservacao_etapa_anterior.json` comprova a igualdade dos 35 arquivos anteriores por SHA-256, incluindo o README. Como o enunciado pede atualização do README, a equipe precisará decidir antes do envio se poderá acrescentar a documentação da nova etapa; o texto está preparado separadamente em `LEIA_ME_ETAPA_ATUAL.md` e não foi aplicado ao arquivo anterior.

Envie o conteúdo da pasta, sem criar outra pasta `Projeto_Big_Data` dentro do repositório e sem usar o ZIP como substituto dos arquivos navegáveis. Nunca selecione `.git/`, `.terraform/`, `.venv/`, `__pycache__/`, `tmp/`, state, `terraform.tfvars`, senhas, tokens ou a pasta `segredos/` no upload. O `.gitignore` não filtra arquivos arrastados manualmente no navegador. A pasta `resultados/` deve conter a base compactada; o CSV extraído e os intermediários locais não precisam ser enviados.

Envie na plataforma da disciplina o link do repositório atualizado, conforme o procedimento da turma. O pacote e o guia não substituem o banco provisionado com a carga.

Ao terminar, remova `AIVEN_TOKEN` e `PGPASSWORD` da sessão ou feche a janela. Preserve o serviço durante o período em que será avaliado; planos gratuitos podem ser desligados por inatividade, conforme as regras do provedor.

Fontes: [plano gratuito e limites](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier), [criação de serviço](https://aiven.io/docs/products/postgresql/get-started), [provider Terraform](https://registry.terraform.io/providers/aiven/aiven/latest/docs/resources/pg).

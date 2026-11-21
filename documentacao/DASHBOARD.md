# Executar e publicar o painel

## Preparar a conexão

1. Use um PostgreSQL com a carga CAGED validada. O projeto usa Aiven Free e a view `caged.v_indicadores_emprego`. Confira a carga com `python codigo/executar.py verificar-nuvem` a partir da sessão administrativa já configurada. Se o serviço estiver ativo e preenchido, esse comando consulta e registra contagens, hash, TLS e tamanho, com os dados preservados.
2. Crie o usuário `caged_dashboard` no serviço Aiven. Com o proprietário dos objetos de `caged`, execute [permissoes_dashboard.sql](../sql/permissoes_dashboard.sql). O app precisa de uso do schema e leitura da view. Guarde senha, host, porta, banco e CA fora do Git. [Gerenciamento de usuários no Aiven](https://aiven.io/docs/products/postgresql/howto/manage-service-users)
3. Instale as dependências com `python -m pip install -r requirements.txt` em um ambiente virtual Python 3.12. Copie `.env.example` para `.env` e preencha `PG*` com a conta do painel. Em `PGSSLROOTCERT`, use o caminho local do certificado CA. O aplicativo também aceita as variáveis diretamente no ambiente e sempre exige TLS com `verify-full`.

## Executar com um comando

Na raiz do projeto, com o ambiente e a conexão preparados:

```sh
python -m streamlit run dashboard/app.py --server.address localhost
```

Abra o endereço local indicado pelo Streamlit. O botão **Atualizar dados** força uma nova consulta ao PostgreSQL. Em caso de erro, confira o estado do serviço, o filtro de IP, as variáveis e a CA. O painel apresenta um aviso genérico e preserva os dados de acesso.

Para guardar a configuração fora de uma pasta sincronizada, defina `CAGED_ENV_FILE` com o caminho de um arquivo dotenv privado. O `.env` do projeto pode conter apenas esse apontamento.

## Reconciliar o Terraform do banco existente

Use o mesmo backend e arquivo de variáveis privados do projeto, conforme o [guia de infraestrutura](GUIA_IMPLANTACAO.md). Carregue o token Aiven na sessão e confirme o recurso com `terraform -chdir=infraestrutura state list`. Se `aiven_pg.caged` já apontar para o serviço correto, faça um plano com atualização do estado. Se estiver ausente, importe o serviço existente uma vez com a configuração correspondente.

```powershell
$arquivoVariaveisCaged = Join-Path $env:LOCALAPPDATA 'ProjetoBigData/terraform.entrega.tfvars.json'
terraform -chdir=infraestrutura plan -var-file="$arquivoVariaveisCaged" -detailed-exitcode
```

Numa instalação nova, prepare o arquivo privado a partir de [terraform.tfvars.example](../infraestrutura/terraform.tfvars.example) e aponte para ele em `-var-file`. Use extensão `.tfvars` para HCL ou `.tfvars.json` para JSON.

O código de saída 0 indica ausência de mudanças, 2 indica mudanças propostas e 1 indica falha. Para mudanças esperadas, como a inclusão de um IP específico no filtro, faça o `apply` do plano revisado e rode o plano novamente. Uma proposta de substituição exige verificar os nomes, o plano, o backend e o serviço antes de aplicar. O bloco `prevent_destroy` protege o serviço no Terraform. A variável `termination_protection` controla a proteção no Aiven e pode refletir o valor existente quando o serviço é importado.

Na entrega foi usado o state privado existente e um arquivo privado de variáveis com os parâmetros conferidos na API. O ajuste adicionou o IPv6 do navegador como `/128`. A API, o state e o plano final foram conferidos depois da aplicação. [Registro da reconciliação](../verificacoes/terraform_entrega.json) · [Autorização de IP no PG Studio](https://aiven.io/docs/products/postgresql/howto/pg-studio/security-connections)

## Publicar no Streamlit Community Cloud

1. Disponibilize a branch de entrega no GitHub. No Community Cloud, selecione essa branch e `dashboard/app.py` como ponto de entrada. O serviço instala `requirements.txt` da raiz. [Implantação no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
2. Em **Advanced settings → Secrets**, defina `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` e `PGPASSWORD` com os dados da conta de leitura. Defina `PGSSLROOTCERT_PEM` com o PEM da CA, em uma string TOML multilinha. A aplicação escreve a CA em um arquivo temporário durante a conexão e o remove em seguida. [Segredos do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
3. Confira a lista de IPs de saída publicada pelo Streamlit. Inclua os CIDRs aplicáveis em `allowed_cidrs` no arquivo privado do Terraform. Compare o plano e aplique a mudança ao serviço existente. [IPs do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/status#ip-addresses)
4. Abra o painel publicado e teste um recorte com mudanças de filtros em cada indicador. Use **Atualizar dados** para verificar nova consulta ao Aiven. Registre o link ativo no README após a conferência.

Os recursos do PostgreSQL estão em [infraestrutura/](../infraestrutura/). A publicação opcional do painel usa a configuração Streamlit versionada e os segredos da plataforma.

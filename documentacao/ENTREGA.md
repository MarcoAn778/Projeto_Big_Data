# Mapa da entrega final

| Entregável | Artefatos |
| --- | --- |
| Painel com consulta direta ao banco | [Streamlit](../dashboard/app.py), [consultas](../dashboard/consultas.py), [metodologia](INDICADORES.md) |
| Execução e publicação | [Comando local e implantação opcional](DASHBOARD.md) |
| Infraestrutura e carga | [Terraform](../infraestrutura/), [conciliação do state](../verificacoes/terraform_entrega.json), [conferência atual da carga](../verificacoes/carga_nuvem.json) |
| README, arquitetura e análise crítica | [README](../README.md), [modelagem](MODELAGEM.md), [SQL de reprodução](../sql/analise_ods.sql) |
| Testes e segurança | [Testes](../testes/), [validação](VALIDACAO.md), [gestão de acessos](SEGURANCA.md) |
| Apresentação | [Roteiro de 10 minutos](PITCH.md) |

O enunciado da entrega final aceita o comando local como alternativa ao link publicado. A execução usa PostgreSQL no Aiven e a hospedagem do Streamlit é opcional. A carga foi conferida em 21/11/2026. Use `verificar-nuvem` para repetir a verificação antes da apresentação.

## Preparar a entrega

1. Confira o serviço e a configuração do Terraform, com o state privado.
2. Valide o banco e rode os testes de leitura. Teste os quatro indicadores com filtros e atualize a consulta na interface.
3. Verifique o índice com `python codigo/verificar_segredos.py`. Gere o pacote com `python codigo/preparar_envio.py` para o fluxo de envio manual. O modo `--rascunho` prepara uma cópia de revisão enquanto a conferência ao vivo estiver pendente.
4. Abra o README na versão enviada e ensaie a demonstração.

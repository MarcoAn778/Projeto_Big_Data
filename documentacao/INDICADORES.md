# Indicadores de emprego formal

O projeto investiga como admissões, desligamentos e salários de entrada se distribuem por sexo e raça/cor no emprego formal brasileiro. O cruzamento por mês, território, setor e faixa etária permite identificar diferenças de participação e remuneração relevantes para a ODS 5, de igualdade de gênero, e para a ODS 18 brasileira, de igualdade étnico-racial. A unidade analisada é a movimentação, que pode ocorrer mais de uma vez para uma mesma pessoa.

| Indicador | Cálculo e recorte | Leitura |
| --- | --- | --- |
| Saldo mensal | Soma de admissões menos soma de desligamentos por competência, sexo e raça/cor | Valor positivo indica expansão líquida dos fluxos observados naquele grupo. |
| Turnover setorial | Soma de desligamentos dividida pela soma de admissões, por competência, seção CNAE, sexo e raça/cor | A referência 1 indica igualdade entre fluxos. Sem admissões, a razão fica indefinida. A tabela mostra as duas contagens. |
| Salário médio de admissão | Nas linhas de admissão, soma de `soma_salarios_validos` dividida pela soma de `quantidade_salarios_validos`, por sexo e raça/cor | O painel exibe a média em reais, o número de salários válidos e a razão percentual frente à maior média no recorte. Sem salários válidos a média é indefinida. Se a maior média for zero, a razão fica indefinida. |
| Participação por setor | Admissões ou desligamentos da categoria divididos pelo total do mesmo fluxo no setor | Mulheres usam o código de sexo 3. Pessoas negras reúnem os códigos de raça/cor 2 (preta) e 3 (parda). A série de mulheres aplica o filtro de raça/cor ao numerador e ao denominador. A série de pessoas negras aplica o filtro de sexo a ambos. |

Competência, região, UF, seção CNAE e faixa etária recortam todos os indicadores. Sexo e raça/cor filtram diretamente os três primeiros. Na participação, cada filtro demográfico permite estratificar a série da outra dimensão. Sem filtro de raça/cor, todos os eventos elegíveis entram no denominador aplicável, incluindo **Não informada** (código 6) e **Não identificado** (código 9). As duas categorias têm rótulos e opções separados no painel.

O recorte usa os arquivos MOV do Novo CAGED, de agosto de 2025 a julho de 2026. FOR, EXC e revisões posteriores ficam fora. MOV registra fluxos do emprego formal e carece de estoque de vínculos, que seria necessário para estimar uma taxa convencional de rotatividade. A média usa valores nominais, sem controle de ocupação, escolaridade ou jornada. Os salários iguais a zero entram no cálculo. Valores negativos, ausentes ou recusados na conversão ficam de fora da média, com a movimentação preservada nas contagens.

O painel consulta diretamente a view PostgreSQL `caged.v_indicadores_emprego`. Os resultados ficam em cache por até 60 segundos. **Atualizar dados** invalida o cache para uma nova consulta. A hora exibida registra quando os dados daquele recorte foram consultados.

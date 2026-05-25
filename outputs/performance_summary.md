# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 12.185 | 14.190 | 261 |
| Tabela agregada | 7 | 3.878 | 4.913 | 261 |

Ganho médio observado: 2.89x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

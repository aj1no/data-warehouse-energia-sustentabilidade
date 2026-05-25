# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 8.307 | 9.497 | 261 |
| Tabela agregada | 7 | 2.607 | 3.878 | 261 |

Ganho médio observado: 2.45x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

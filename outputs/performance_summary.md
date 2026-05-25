# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 8.725 | 9.764 | 261 |
| Tabela agregada | 7 | 2.959 | 3.149 | 261 |

Ganho médio observado: 3.10x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

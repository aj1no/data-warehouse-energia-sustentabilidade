# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 8.648 | 9.302 | 261 |
| Tabela agregada | 7 | 2.722 | 3.034 | 261 |

Ganho médio observado: 3.07x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

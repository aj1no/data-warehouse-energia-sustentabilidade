# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 7.434 | 8.788 | 261 |
| Tabela agregada | 7 | 2.442 | 2.685 | 261 |

Ganho médio observado: 3.27x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 8.843 | 10.138 | 261 |
| Tabela agregada | 7 | 2.639 | 3.002 | 261 |

Ganho médio observado: 3.38x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

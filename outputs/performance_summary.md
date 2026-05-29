# Resultados de Performance

Autores: Dalmir Doneda Júnior; Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | 7 | 6.973 | 7.730 | 261 |
| Tabela agregada | 7 | 2.473 | 2.778 | 261 |

Ganho médio observado: 2.78x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.

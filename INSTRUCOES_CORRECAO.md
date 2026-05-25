# Correção manual para o GitHub - versão sem .deps

Esta versão remove do run_all.py a tentativa de carregar bibliotecas pela pasta .deps.

Motivo:
O erro PermissionError em .deps/pandas/__init__.py ocorre porque o Python está tentando importar o pandas de uma pasta local .deps corrompida, bloqueada ou sem permissão. Como as dependências já foram instaladas com pip install -r requirements.txt, a pasta .deps não é necessária.

Como usar:

1. Extraia este ZIP dentro da pasta local do repositório:
   data-warehouse-energia-sustentabilidade

2. Aceite substituir os arquivos existentes.

3. Apague a pasta .deps, se ela existir:

   PowerShell:
   Remove-Item -Recurse -Force .\.deps

   Se não conseguir apagar, feche o VS Code/terminal, abra novamente e tente:
   Rename-Item .\.deps .deps_old

4. Rode os testes:

   python -m py_compile run_all.py
   python -c "import pandas, duckdb; print('pandas ok', pandas.__version__); print('duckdb ok', duckdb.__version__)"
   python run_all.py

5. Se der certo, envie ao GitHub:

   git add .
   git commit -m "Remove dependencia local .deps do run_all"
   git push origin main

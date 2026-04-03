# Ajuda dos Scripts Automáticos

Esta pasta contém ferramentas automáticas para auxiliar na organização de jogos e mídias do EmulationStation/Retrobat.
A longo prazo, cada script será acompanhado de um arquivo `.exe` portátil para facilitar o uso sem a necessidade de instalação de dependências.

---

## 1. Create_gamelist.py

**Para que serve:**
Gera automaticamente um arquivo `gamelist.xml` para um determinado sistema. Ele buscará por todos os jogos (baseado nas extensões que você quiser) e criará no `gamelist.xml` as tags para vincular os jogos às suas respectivas mídias: `fanart (.jpg)`, `video (.mp4)`, `logo (.png)` e `cover (.png)`. Ele faz esse vínculo mesmo que as mídias físicas ainda não existam.

**Como usar via CMD/Terminal:**
```cmd
python Create_gamelist.py [Caminho do Sistema] [Extensões]
```
Exemplo:
```cmd
python Create_gamelist.py "Y:\images\RIESCADE\roms\mame" zip 7z chd
```

**Para exibir os comandos de ajuda:**
```cmd
python Create_gamelist.py -h
```

---

## 2. setup_system_media.ps1 (Pasta raiz)

**Para que serve:**
Para pastas com apenas 1 jogo ("jogos soltos" e temas customizados). Este script busca pelas imagens do *"Tema Global"* nas pastas `arts (.jpg)` e `logos (.png)`, e copia esses arquivos diretamente para `media/fanart` e `media/logo` de uma pasta rom específica que você informar. Ele renomeia o arquivo baseado no nome do sistema e automaticamente atualiza a `gamelist.xml` daquele sistema específico para refletir a imagem e logo originais do tema.

**Como usar via Powershell:**
```cmd
powershell.exe -ExecutionPolicy Bypass -File "Y:\images\RIESCADE\setup_system_media.ps1" -systemFolder "Y:\images\RIESCADE\roms\nome_do_sistema"
```

---

## 3. Compare_files.py

**Para que serve:**
Utilitário simples que compara os arquivos entre duas pastas. Ele verifica e lista quais arquivos presentes na "Pasta 1" (primeiro parâmetro) também existem na "Pasta 2" (segundo parâmetro).

**Como usar via CMD/Terminal:**
Você pode informar os nomes dos sistemas diretamente (que fará a busca em `y:\images\RIESCADE\roms\[sistema]`) ou os caminhos completos:
```cmd
python Compare_files.py [Pasta/Sistema 1] [Pasta/Sistema 2]
```
Exemplo simplificado:
```cmd
python Compare_files.py snes mame
```
Exemplo com caminhos completos:
```cmd
python Compare_files.py "Y:\images\RIESCADE\roms\mame" "C:\backup\mame"
```

---

## 4. Diagnostics.py

**Para que serve:**
Executa um diagnóstico completo do sistema e exibe as estatísticas e as perdas na tela do terminal. Este script verifica os arquivos de configuração `es_systems*.cfg` e faz análises baseadas nas ROMs presentes no disco. 
Verificações realizadas:
- **Sistemas Vazios:** Aponta sistemas declarados, mas sem ROMs (mesmo que as pastas contenham apenas `metadata.txt` e `systeminfo.txt`).
- **Artes de Sistemas e Temas:** Procura por ausência de imagens correspondentes de background e logotipos do sistema base comparados com a pasta de temas global (`themes/arts` e `themes/logos`).
- **Artes de Coleções:** Alerta se uma coleção listada na pasta `collections` não tiver artes e logos também presentes no tema global.
- **ROMs Faltando Medias:** Compara todos os jogos e os seus metadados nos arquivos `gamelist.xml` com a existência física de arquivos de mídia (`fanart`, `logo`, `video`, `cover`).

**Como usar via CMD/Terminal:**
```cmd
python Diagnostics.py
```

Para gerar um arquivo em texto (`Diagnostics.log`) com os resultados na mesma pasta:
```cmd
python Diagnostics.py -log
```

Para verificar os dados de um sistema individualmente (por exemplo, "snes"):
```cmd
python Diagnostics.py -platform snes
```

Podendo ainda combinar os comandos:
```cmd
python Diagnostics.py -platform snes -log
```

---

*(Mais scripts podem ser adicionados e documentados aqui conforme a necessidade do sistema crescer)*

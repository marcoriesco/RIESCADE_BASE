import os
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="""
=========================================================
GERADOR DE GAMELIST.XML
=========================================================
Cria uma gamelist.xml listando todos os jogos encontrados
na pasta e aponta as midias para as pastas fanart, logo, 
video e cover padrao de acordo com o nome do arquivo.
""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("folder", help="Caminho para a pasta onde estao os jogos.")
    parser.add_argument("extensions", nargs='+', help="Uma ou mais extensoes para procurar (ex: zip 7z chd).")
    
    args = parser.parse_args()
    
    folder = args.folder
    if not os.path.exists(folder) or not os.path.isdir(folder):
        print(f"Erro: A pasta do sistema '{folder}' nao existe.")
        return
        
    # Garante que as extensoes tenham um '.' no inicio (ex: "zip" vira ".zip")
    exts = [ext.lower() if ext.startswith('.') else f".{ext.lower()}" for ext in args.extensions]
    
    gamelist_path = os.path.join(folder, "gamelist.xml")
    
    # Montagem simples da gamelist em XML
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<gameList>'
    ]
    
    count = 0
    # Processa cada arquivo da pasta em ordem alfabetica
    items = sorted(os.listdir(folder))
    for item in items:
        item_path = os.path.join(folder, item)
        if os.path.isfile(item_path):
            name, ext = os.path.splitext(item)
            if ext.lower() in exts:
                count += 1
                xml_lines.append('  <game>')
                xml_lines.append(f'    <path>./{item}</path>')
                xml_lines.append(f'    <name>{name}</name>')
                xml_lines.append( '    <desc></desc>')
                xml_lines.append(f'    <image>./media/fanart/{name}.jpg</image>')
                xml_lines.append(f'    <video>./media/video/{name}.mp4</video>')
                xml_lines.append(f'    <marquee>./media/logo/{name}.png</marquee>')
                xml_lines.append(f'    <thumbnail>./media/cover/{name}.png</thumbnail>')
                xml_lines.append('  </game>')
                
    xml_lines.append('</gameList>')
    xml_lines.append('') # Nova linha ao final do arquivo
    
    if count == 0:
        print("Aviso: Nenhum jogo foi encontrado para as extensoes fornecidas.")
        
    # Salva o arquivo em disco
    with open(gamelist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
        
    print(f"Pronto! gamelist.xml com {count} jogo(s) gerada com sucesso em:\n{gamelist_path}")

if __name__ == "__main__":
    main()

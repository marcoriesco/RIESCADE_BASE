import os
import argparse
import glob
import xml.etree.ElementTree as ET

# Paths (Relativos para Portabilidade)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ES_SYSTEMS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
ROOT_DIR = os.path.abspath(os.path.join(ES_SYSTEMS_DIR, "..", ".."))

def get_system_path(system_name):
    cfg_files = glob.glob(os.path.join(ES_SYSTEMS_DIR, "es_systems*.cfg"))
    for cfg_file in cfg_files:
        try:
            tree = ET.parse(cfg_file)
            root = tree.getroot()
            for system in root.findall('system'):
                name_elem = system.find('theme')
                path_elem = system.find('path')
                if name_elem is not None and path_elem is not None:
                    name = name_elem.text.strip() if name_elem.text else ""
                    if name.lower() == system_name.lower():
                        path = path_elem.text.strip() if path_elem.text else ""
                        # Clean path
                        path = path.replace("~\\..\\", ROOT_DIR + "\\")
                        path = path.replace("~/../", ROOT_DIR + "\\").replace("~/", ES_SYSTEMS_DIR + "\\")
                        return os.path.normpath(path)
        except Exception:
            pass
    # Fallback caso nao encontre no cfg
    return os.path.join(ROOT_DIR, "roms", system_name)

def main():
    parser = argparse.ArgumentParser(
        description="""
=========================================================
GERADOR DE GAMELIST.XML
=========================================================
Cria uma gamelist.xml listando todos os jogos encontrados
no sistema e aponta as midias para as pastas fanart, logo, 
video e cover padrao de acordo com o nome do arquivo/pasta.
""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-f", "--folders", action="store_true", help="Procura por diretorios ao inves de arquivos.")
    parser.add_argument("system", help="Nome do sistema (ex: snes, teknoparrot).")
    parser.add_argument("extensions", nargs='+', help="Uma ou mais extensoes para procurar (ex: zip 7z chd).")
    
    args = parser.parse_args()
    
    folder = get_system_path(args.system)
    
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
    # Processa cada arquivo/pasta da pasta em ordem alfabetica
    items = sorted(os.listdir(folder))
    for item in items:
        item_path = os.path.join(folder, item)
        
        is_target = False
        if args.folders:
            is_target = os.path.isdir(item_path)
        else:
            is_target = os.path.isfile(item_path)
            
        if is_target:
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
        tipo = "diretorios" if args.folders else "arquivos"
        print(f"Aviso: Nenhum jogo ({tipo}) foi encontrado para as extensoes fornecidas no sistema {args.system}.")
        
    # Salva o arquivo em disco
    with open(gamelist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_lines))
        
    print(f"Pronto! gamelist.xml com {count} jogo(s) gerada com sucesso em:\n{gamelist_path}")

if __name__ == "__main__":
    main()

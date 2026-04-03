import os
import xml.etree.ElementTree as ET
import glob
import argparse
import sys

# Paths (Relativos para Portabilidade)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# ES_SYSTEMS_DIR: sobe _scripts -> resources -> RIESCADE_ORIGINS -> themes -> .emulationstation
ES_SYSTEMS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

# ROOT_DIR: sobe .emulationstation -> emulationstation -> RAIZ (RIESCADE)
ROOT_DIR = os.path.abspath(os.path.join(ES_SYSTEMS_DIR, "..", ".."))
ROMS_DIR = os.path.join(ROOT_DIR, "roms")

THEMES_ARTS_DIR = os.path.join(ES_SYSTEMS_DIR, "themes", "arts")
THEMES_LOGOS_DIR = os.path.join(ES_SYSTEMS_DIR, "themes", "logos")
COLLECTIONS_DIR = os.path.join(ES_SYSTEMS_DIR, "collections")

class Logger(object):
    def __init__(self, filename="Diagnostics.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def main():
    parser = argparse.ArgumentParser(description="Executa o diagnostico completo do sistema.")
    parser.add_argument("-log", action="store_true", help="Salva a saida do console em um arquivo Diagnostics.log")
    parser.add_argument("-platform", type=str, help="Filtra a busca apenas para um determinado sistema (ex: snes, mame)", default=None)
    parser.add_argument("-systems", action="store_true", help="Diagnostica apenas os sistemas e colecoes que faltam logos e arts")
    args = parser.parse_args()

    if args.log:
        sys.stdout = Logger()

    print("=========================================================")
    print("           DIAGNOSTICO COMPLETO DO SISTEMA               ")
    print("=========================================================\n")

    # Parse es_systems.cfg and all es_systems_*.cfg
    cfg_files = glob.glob(os.path.join(ES_SYSTEMS_DIR, "es_systems*.cfg"))
    
    systems = []

    for cfg_file in cfg_files:
        try:
            tree = ET.parse(cfg_file)
            root = tree.getroot()
            for system in root.findall('system'):
                name_elem = system.find('theme')
                path_elem = system.find('path')
                ext_elem = system.find('extension')
                
                if name_elem is not None and path_elem is not None:
                    name = name_elem.text.strip() if name_elem.text else ""
                    path = path_elem.text.strip() if path_elem.text else ""
                    exts = ext_elem.text.strip().split() if (ext_elem is not None and ext_elem.text) else []
                    
                    # Clean path
                    # Substitui as mascaras de diretorio do Retrobat pela nossa raiz dinamica portátil
                    path = path.replace("~\\..\\", ROOT_DIR + "\\")
                    path = path.replace("~/../", ROOT_DIR + "\\").replace("~/", ES_SYSTEMS_DIR + "\\")
                    path = os.path.normpath(path)
                    
                    systems.append({
                        "name": name,
                        "path": path,
                        "extensions": exts
                    })
        except Exception as e:
            print(f"Erro ao ler {cfg_file}: {e}")

    if args.platform:
        systems = [s for s in systems if s["name"].lower() == args.platform.lower()]

    if not args.platform:
        # 1. Logos e arts de sistemas faltando
        print("--- SISTEMAS: ARTES E LOGOS FALTANDO ---")
        missing_sys_arts = []
        missing_sys_logos = []
        
        for sys in systems:
            sys_name = sys["name"]
            
            # Check Arts
            art_matches = glob.glob(os.path.join(THEMES_ARTS_DIR, f"{sys_name}.*"))
            if not art_matches:
                missing_sys_arts.append(sys_name)
                
            # Check Logos
            logo_matches = glob.glob(os.path.join(THEMES_LOGOS_DIR, f"{sys_name}.*"))
            if not logo_matches:
                missing_sys_logos.append(sys_name)

        print(f"Sistemas faltando Arts ({len(missing_sys_arts)}): {', '.join(missing_sys_arts) if missing_sys_arts else 'Nenhum'}")
        print(f"Sistemas faltando Logos ({len(missing_sys_logos)}): {', '.join(missing_sys_logos) if missing_sys_logos else 'Nenhum'}")
        print("\n")

        # 2. Colecoes faltando artes
        print("--- COLECOES: ARTES E LOGOS FALTANDO ---")
        missing_col_arts = []
        missing_col_logos = []
        
        col_files = glob.glob(os.path.join(COLLECTIONS_DIR, "*.cfg"))
        for col_file in col_files:
            col_name = os.path.splitext(os.path.basename(col_file))[0]
            
            # Check Arts
            art_matches = glob.glob(os.path.join(THEMES_ARTS_DIR, f"{col_name}.*"))
            if not art_matches:
                missing_col_arts.append(col_name)
                
            # Check Logos
            logo_matches = glob.glob(os.path.join(THEMES_LOGOS_DIR, f"{col_name}.*"))
            if not logo_matches:
                missing_col_logos.append(col_name)

        print(f"Colecoes faltando Arts ({len(missing_col_arts)}): {', '.join(missing_col_arts) if missing_col_arts else 'Nenhum'}")
        print(f"Colecoes faltando Logos ({len(missing_col_logos)}): {', '.join(missing_col_logos) if missing_col_logos else 'Nenhum'}")
        print("\n")

    if args.systems:
        return

    # 3. Sistemas vazios sem roms e ROMs faltando medias
    print("--- STATUS DAS ROMS E MEDIAS POR SISTEMA ---")
    empty_systems = []
    
    for sys in systems:
        sys_name = sys["name"]
        rom_dir = sys["path"]
        exts = [ext.lower() for ext in sys["extensions"]]
        
        if not os.path.exists(rom_dir) or not os.path.isdir(rom_dir):
            empty_systems.append(sys_name)
            continue
            
        rom_files = []
        # First pass: identify top-level directories that ARE roms (e.g. .teknoparrot folders)
        rom_dirs_set = set()
        if exts:
            for item in os.listdir(rom_dir):
                item_path = os.path.join(rom_dir, item)
                if os.path.isdir(item_path):
                    _, dir_ext = os.path.splitext(item)
                    if dir_ext.lower() in exts:
                        rom_files.append(item_path)
                        rom_dirs_set.add(item_path)
        
        # Second pass: walk for file-based roms, skipping rom directories and media folders
        for root, dirs, files in os.walk(rom_dir):
            # Skip media folders
            if "media" in root.lower().split(os.sep):
                continue
            # Prune directories that are rom-directories so we don't recurse into them
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in rom_dirs_set]
            for file in files:
                if file.lower() in ("metadata.txt", "systeminfo.txt", "gamelist.xml"):
                    continue
                _, file_ext = os.path.splitext(file)
                if exts and file_ext.lower() in exts:
                    rom_files.append(os.path.join(root, file))
                elif not exts:
                    rom_files.append(os.path.join(root, file))
                    
        if not rom_files:
            empty_systems.append(sys_name)
            continue

        gamelist_path = os.path.join(rom_dir, "gamelist.xml")
        gamelist_data = {} 
        if os.path.exists(gamelist_path):
            try:
                tree = ET.parse(gamelist_path)
                root = tree.getroot()
                for game in root.findall("game"):
                    path_elem = game.find("path")
                    if path_elem is not None and path_elem.text:
                        rom_rel_path = os.path.normpath(path_elem.text)
                        
                        if rom_rel_path.startswith("." + os.sep) or rom_rel_path.startswith("./") or rom_rel_path.startswith(".\\"):
                            rom_full = os.path.normpath(os.path.join(rom_dir, rom_rel_path[2:]))
                        else:
                            rom_full = os.path.normpath(os.path.join(rom_dir, rom_rel_path))

                        img = game.find("image")
                        marq = game.find("marquee")
                        vid = game.find("video")
                        thumb = game.find("thumbnail")
                        
                        gamelist_data[rom_full] = {
                            "image": img.text if img is not None else None,
                            "marquee": marq.text if marq is not None else None,
                            "video": vid.text if vid is not None else None,
                            "thumbnail": thumb.text if thumb is not None else None
                        }
            except Exception as e:
                pass 

        missing_rom_media = []
        for rom_full in rom_files:
            rom_rel = os.path.relpath(rom_full, rom_dir)
            
            if rom_full not in gamelist_data:
                missing_rom_media.append(f"{rom_rel} (Falta gamelist.xml/tags: todas medias)")
            else:
                data = gamelist_data[rom_full]
                missing_tags = []
                
                def check_media_tag(tag, tag_name):
                    if not tag:
                        return True 
                    
                    if tag.startswith("./") or tag.startswith(".\\"):
                        media_full = os.path.normpath(os.path.join(rom_dir, tag[2:]))
                    else:
                        media_full = os.path.normpath(os.path.join(rom_dir, tag))
                    
                    return not os.path.exists(media_full)
                    
                if check_media_tag(data["image"], "fanart"): missing_tags.append("fanart")
                if check_media_tag(data["marquee"], "logo"): missing_tags.append("logo")
                if check_media_tag(data["video"], "video"): missing_tags.append("video")
                if check_media_tag(data["thumbnail"], "cover"): missing_tags.append("cover")
                
                if missing_tags:
                    missing_rom_media.append(f"{rom_rel} -> PENDENTE: {', '.join(missing_tags)}")
                    
        if missing_rom_media:
            print(f"[{sys_name}] {len(missing_rom_media)} ROM(s) com midias pendentes:")
            for m in missing_rom_media:
                print(f"  - {m}")
                
    if not args.platform:
        print("\n--- SISTEMAS VAZIOS ---")
        print(f"Sistemas sem roms cadastradas ou pastas vazias ({len(empty_systems)}):")
        if empty_systems:
            for es_sys in empty_systems:
                print(f"  - {es_sys}")
        else:
            print("Nenhum")

if __name__ == "__main__":
    main()

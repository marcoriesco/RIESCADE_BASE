import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Compara duas pastas para saber quais arquivos da pasta 1 existem na pasta 2.")
    parser.add_argument("pasta1", help="Caminho para a primeira pasta ou o nome do sistema (ex: snes)")
    parser.add_argument("pasta2", help="Caminho para a segunda pasta ou o nome do sistema (ex: mame)")
    
    args = parser.parse_args()
    
    def resolve_path(arg):
        if "\\" in arg or "/" in arg:
            return Path(arg)
        # Se for apenas um nome, assume que é uma pasta em roms resolvendo dinamicamente
        script_dir = Path(__file__).resolve().parent
        # Sobe: _scripts(0) -> resources(1) -> ORIGINS(2) -> themes(3) -> .emulationstation(4) -> emulationstation(5) -> RAIZ
        roms_dir = script_dir.parents[5] / "roms" 
        return roms_dir / arg
        
    path1 = resolve_path(args.pasta1)
    path2 = resolve_path(args.pasta2)
    
    if not path1.is_dir():
        print(f"Erro: A pasta '{path1}' não existe ou não é um diretório.")
        return
        
    if not path2.is_dir():
        print(f"Erro: A pasta '{path2}' não existe ou não é um diretório.")
        return
        
    # Obtém apenas os nomes dos arquivos (ignorando subpastas). 
    # Mapeia tudo para minúsculo para evitar divergências de maiúsculas/minúsculas no Windows
    files1 = {f.name.lower(): f.name for f in path1.iterdir() if f.is_file()}
    files2_lower = {f.name.lower() for f in path2.iterdir() if f.is_file()}
    
    # Identifica arquivos da pasta 1 que também existem na pasta 2
    common_files = [original_name for lower_name, original_name in files1.items() if lower_name in files2_lower]
    
    print(f"=== Comparando Arquivos ===")
    print(f"Pasta 1: {path1} ({len(files1)} arquivos)")
    print(f"Pasta 2: {path2} ({len(files2_lower)} arquivos)")
    print("-" * 40)
    
    if not common_files:
        print("Nenhum arquivo da Pasta 1 foi encontrado na Pasta 2.")
    else:
        print(f"Encontrado(s) {len(common_files)} arquivo(s) da Pasta 1 que estão presentes na Pasta 2:\n")
        for f in sorted(common_files, key=lambda x: x.lower()):
            print(f" - {f}")

if __name__ == "__main__":
    main()

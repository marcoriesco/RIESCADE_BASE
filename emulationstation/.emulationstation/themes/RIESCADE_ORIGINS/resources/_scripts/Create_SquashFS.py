import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Creates squashfs files from directories.")
    parser.add_argument("system", nargs="?", help="System name (e.g. snes-msu1)")
    
    args = parser.parse_args()
    
    if not args.system:
        print("Uso: python Create_SquashFS.py <nome-do-sistema>")
        print("Exemplo: python Create_SquashFS.py snes-msu1")
        sys.exit(1)
        
    system_name = args.system
    # Pasta raiz contendo os sistemas
    base_dir = r"/mnt/y/images/RIESCADE/roms"
    system_folder = os.path.join(base_dir, system_name)
    
    if not os.path.isdir(system_folder):
        print(f"[Erro] A pasta do sistema '{system_folder}' nao foi encontrada.")
        sys.exit(1)
        
    print(f"Iniciando conversao para o sistema: {system_name}")
    print(f"Buscando pastas em: {system_folder}\n")
    
    count = 0
    # Iterando sobre cada item na pasta do sistema
    for item in os.listdir(system_folder):
        item_path = os.path.join(system_folder, item)
        
        # O mksquashfs sera aplicado apenas em diretorios
        if os.path.isdir(item_path):
            count += 1
            
            # Checa se a pasta tem uma "extensao" e que nao contenha espacos. 
            # Isso evita que "Super Mario Bros. 3" perca o ". 3", mas "jogo.windows" perca ".windows".
            base_name, ext = os.path.splitext(item)
            if ext and " " not in ext:
                nome_final = base_name
            else:
                nome_final = item
                
            squash_filename = f"{nome_final}.wsquashfs"
            squash_filepath = os.path.join(system_folder, squash_filename)
            
            print(f"[*] Processando: {item} -> {squash_filename}")
            
            # Configs solicitadas: -comp xz -b 1M -Xdict-size 100%
            cmd = [
                "mksquashfs",
                item_path,
                squash_filepath,
                "-comp", "xz",
                "-b", "1M",
                "-Xdict-size", "100%"
            ]
            
            try:
                # O shell=True as vezes exige a linha de comando como string no Windows para resolucao correta
                subprocess.run(" ".join([f'"{c}"' if " " in c or ":" in c else c for c in cmd]), check=True, shell=True)
                print(f"[+] Sucesso: {squash_filename} criado.\n")
            except subprocess.CalledProcessError as e:
                print(f"[-] Erro ao criar {squash_filename}: Codigo {e.returncode}\n")
            except FileNotFoundError:
                print("[-] Erro critico: executavel 'mksquashfs' nao encontrado. Verifique se ele esta no PATH do Windows.\n")
                sys.exit(1)
                
    if count == 0:
        print("Nenhuma pasta foi encontrada para converter.")
    else:
        print("Processamento concluido com sucesso!")

if __name__ == "__main__":
    main()

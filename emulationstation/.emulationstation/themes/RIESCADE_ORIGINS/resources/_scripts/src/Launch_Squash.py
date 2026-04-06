import os
import sys
import subprocess
import time
import signal

# Configurações globais
MOUNT_EXE = r".\..\..\emulationstation\mount.exe"
DRIVE_LETTER = "Z"

def kill_process_by_name(process_name):
    """Encerra processos pelo nome para garantir uma montagem limpa."""
    try:
        subprocess.run(["taskkill", "/f", "/im", process_name], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def wait_for_drive(drive_path, timeout=20):
    """Aguarda o drive ficar disponível no sistema."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(drive_path):
            return True
        time.sleep(1)
    return False

def get_autorun_params(drive_root):
    """Lê o arquivo autorun.cmd e extrai DIR e CMD."""
    autorun_path = os.path.join(drive_root, "autorun.cmd")
    params = {"DIR": "", "CMD": ""}
    
    if not os.path.exists(autorun_path):
        return None

    try:
        with open(autorun_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    params[key.upper()] = val.replace('"', '')
    except Exception as e:
        print(f"Erro ao ler autorun.cmd: {e}")
        return None
        
    return params

def is_drive_in_use(drive_letter):
    """Verifica via tasklist se existe algum processo rodando a partir do drive especificado."""
    try:
        # Busca por processos cujo caminho de execução comece com a letra do drive
        cmd = 'tasklist /v /fo csv'
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')

        # Procura por processos que contenham o drive no caminho
        for line in output.splitlines():
            if f'{drive_letter}:' in line.upper():
                return True
        return False
    except:
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python Launch_Squash.py <caminho_da_rom>")
        sys.exit(1)

    rom_path = sys.argv[1]
    drive_root = f"{DRIVE_LETTER}:\\"

    print(f"--- SquashFS Launcher ---")
    print(f"ROM: {rom_path}")

    # 1. Limpeza inicial
    print("Garantindo ambiente limpo...")
    kill_process_by_name("mount.exe")
    time.sleep(1)

    # 2. Montagem
    print(f"Montando em {drive_root}...")
    try:
        subprocess.Popen([MOUNT_EXE, rom_path, "-drive", DRIVE_LETTER], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Erro ao iniciar mount.exe: {e}")
        sys.exit(1)

    # 3. Aguarda o drive aparecer
    if not wait_for_drive(drive_root):
        print(f"ERRO: Drive {DRIVE_LETTER}: não apareceu após 20 segundos.")
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 4. Lê configurações do jogo
    config = get_autorun_params(drive_root)
    if not config or not config["CMD"]:
        print("ERRO: autorun.cmd inválido ou ausente no drive montado.")
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 5. Prepara execução
    target_dir = os.path.join(drive_root, config["DIR"])
    game_cmd = config["CMD"]

    # Constrói o caminho completo do executável
    game_exe_path = os.path.join(target_dir, game_cmd)

    print(f"Iniciando: {game_exe_path}")
    print(f"Diretório: {target_dir}")

    try:
        # Inicia o jogo
        process = subprocess.Popen(game_exe_path, cwd=target_dir, shell=True)
        
        # Pequena pausa para o processo se estabilizar
        time.sleep(5)
        
        # Loop de monitoramento: Espera enquanto o processo principal OU qualquer 
        # processo rodando do drive Z: estiver ativo.
        print("Aguardando encerramento do jogo...")
        while True:
            # Verifica se o processo inicial ainda existe
            poll = process.poll()
            
            # Mesmo que o processo inicial feche (comum em launchers), 
            # verificamos se ainda há algo rodando do drive Z:
            if poll is not None and not is_drive_in_use(DRIVE_LETTER):
                break
                
            time.sleep(2)

    except Exception as e:
        print(f"Erro durante execução: {e}")
    finally:
        # 6. Desmontagem
        print("Desmontando drive...")
        #kill_process_by_name("mount.exe")
        print("Finalizado com sucesso!")

if __name__ == "__main__":
    main()

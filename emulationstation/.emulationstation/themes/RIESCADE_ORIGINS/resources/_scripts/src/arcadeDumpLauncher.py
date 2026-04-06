import os
import sys
import subprocess
import time
import signal
import shutil
import glob
import psutil
import tempfile
from pathlib import Path

# Configurações globais
MOUNT_EXE = r"mount.exe"
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

def wait_for_process_end(process, drive_letter, timeout=600):
    """
    Aguarda o fim de um processo e valida que o jogo realmente terminou.
    Monitora também se há processos filhos ou conexões com o drive.
    
    Args:
        process: subprocess.Popen object
        drive_letter: letra do drive montado
        timeout: tempo máximo em segundos para aguardar (default 10 min)
    """
    start_time = time.time()
    last_activity_time = time.time()
    inactivity_timeout = 60  # 60 segundos de inatividade antes de considerar finalizado
    
    try:
        while time.time() - start_time < timeout:
            elapsed = time.time() - last_activity_time
            
            # Verifica se o processo original ainda está rodando
            poll = process.poll()
            
            # Verifica se ainda há atividade no drive
            drive_active = is_drive_in_use(drive_letter)
            
            if drive_active:
                # Se ainda há atividade no drive, reseta o contador de inatividade
                last_activity_time = time.time()
            elif poll is not None and elapsed > inactivity_timeout:
                # Se o processo encerrou E passou o timeout de inatividade
                return True
            
            # Debug: mostra status
            process_status = "Ativo" if poll is None else "Finalizado"
            
            time.sleep(3)
        
        # Timeout atingido
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        return False
        
    except KeyboardInterrupt:
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
        return None
        
    return params

def is_drive_in_use(drive_letter):
    """Verifica via psutil se existem processos rodando a partir do drive especificado."""
    try:
        drive_path = f"{drive_letter}:\\"
        
        # Verifica cada processo ativo
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cwd']):
            try:
                # Verifica se o executável ou working directory está no drive
                exe = proc.info.get('exe')
                cwd = proc.info.get('cwd')
                
                if exe and drive_path.upper() in exe.upper():
                    return True
                if cwd and drive_path.upper() in cwd.upper():
                    return True
                    
                # Também verifica os arquivos abertos pelo processo (mais completo)
                try:
                    for file in proc.open_files():
                        if drive_path.upper() in file.path.upper():
                            return True
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        
        return False
    except Exception as e:
        return False

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    rom_path = sys.argv[1]
    drive_root = f"{DRIVE_LETTER}:\\"


    # 1. Limpeza inicial
    kill_process_by_name("mount.exe")
    time.sleep(1)

    # 2. Montagem
    try:
        subprocess.Popen([MOUNT_EXE, rom_path, "-drive", DRIVE_LETTER], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        sys.exit(1)

    # 3. Aguarda o drive aparecer
    if not wait_for_drive(drive_root):
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 4. Lê configurações do jogo
    config = get_autorun_params(drive_root)
    if not config or not config["CMD"]:
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 5. Prepara execução
    target_dir = os.path.join(drive_root, config["DIR"])
    game_cmd = config["CMD"]

    # Constrói o caminho completo do executável
    game_exe_path = os.path.join(target_dir, game_cmd)


    try:
        # Inicia o jogo
        process = subprocess.Popen(game_exe_path, cwd=target_dir, shell=True)
        
        # Pequena pausa para o processo se estabilizar
        time.sleep(5)
        
        # Aguarda o encerramento com melhor detecção
        wait_for_process_end(process, DRIVE_LETTER)

    except Exception as e:
        pass
    finally:
        # 6. Desmontagem
        kill_process_by_name("mount.exe")
        time.sleep(3)
        

if __name__ == "__main__":
    main()

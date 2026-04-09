import os
import sys
import subprocess
import time
import shutil
import psutil
import tempfile
import ctypes
from pathlib import Path

# Configurações globais
MOUNT_EXE = r"Y:\images\RIESCADE\emulationstation\mount.exe"
DRIVE_LETTER = "Z"

def log_output(msg):
    """Imprime mensagens no terminal de forma segura pra quando o console estiver oculto."""
    try:
        print(f"[ArcadeLauncher] {msg}", flush=True)
    except Exception:
        pass

def hide_console():
    """Oculta a janela de terminal do Python (cmd/python.exe)."""
    try:
        if os.name == 'nt':
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

def clean_temp_files():
    """Remove pastas _MEI antigas do PyInstaller, .mountfs e outros lixos retidos."""
    temp_dir = tempfile.gettempdir()
    
    # 1. Limpeza de sujeira do Pyinstaller (_MEI)
    try:
        for item in os.listdir(temp_dir):
            if item.startswith("_MEI"):
                mei_path = os.path.join(temp_dir, item)
                if os.path.isdir(mei_path):
                    try:
                        log_output(f"Limpando pasta temporária órfã vazada no sistema: {item} ...")
                        shutil.rmtree(mei_path)
                    except:
                        pass
    except:
        pass
        
    # 2. Limpeza do cache do mount (.mountfs)
    mountfs_path = os.path.join(temp_dir, ".mountfs")
    if os.path.exists(mountfs_path):
        try:
            log_output("Limpando os arquivos de cache de jogos extraídos na pasta .mountfs ...")
            shutil.rmtree(mountfs_path)
        except Exception as e:
            log_output(f"Aviso: Não foi possível limpar .mountfs. Pode estar em uso. Erro: {e}")

def kill_process_by_name(process_name):
    """Encerra processos pelo nome para garantir uma limpeza total usando treekill."""
    log_output(f"Forçando o encerramento do processo (se existir): {process_name}")
    try:
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
        else:
            creationflags = 0
        subprocess.run(["taskkill", "/f", "/t", "/im", process_name], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=creationflags)
    except:
        pass

def wait_for_drive(drive_path, timeout=20):
    """Aguarda o drive ficar disponível no sistema."""
    log_output(f"Aguardando a montagem do drive {drive_path} ...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(drive_path):
            log_output(f"Drive {drive_path} montado com sucesso e pronto para uso!")
            return True
        time.sleep(1)
    log_output(f"Falha: O tempo limite esgotou aguardando o drive {drive_path}.")
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
                    params[key.upper()] = val.replace('"', '').strip()
    except Exception as e:
        return None
        
    return params

def get_game_exes(target_dir):
    """Mapeia todos os executáveis na MESMA RAIZ do jogo de forma não recursiva para max performance."""
    exes = set()
    try:
        # Troca rglob por glob para fazer a varredura apenas na pasta raiz, sem entrar em subdiretórios
        for path in Path(target_dir).glob("*.exe"):
            exes.add(path.name.lower())
    except Exception:
        pass
    
    # Nomes a serem ignorados caso existam para evitar falso-positivo com o sistema nativo
    generic_exes = {"cmd.exe", "conhost.exe", "timeout.exe", "taskkill.exe", "ping.exe", "choice.exe"}
    return exes - generic_exes

def wait_for_process_end(process, drive_letter, target_dir, script_start):
    """
    Monitora a execução do jogo de maneira aprofundada.
    """
    game_exes = get_game_exes(target_dir)
    drive_path = f"{drive_letter}:\\".upper()
    log_output("O jogo está em execução, iniciando o monitoramento de encerramento do processo principal e subprocessos...")
    
    try:
        while True:
            is_running = False
            
            # 1. Verifica se o cmd do jogo ainda está em execução direta
            if process.poll() is None:
                is_running = True
                
            # 2. Varreduras avançadas do sistema
            if not is_running:
                for proc in psutil.process_iter(['name', 'exe', 'cwd', 'create_time']):
                    try:
                        # Vemos se o exectável ou a pasta base de trabalho ainda chamam nosso Z:\
                        exe = proc.info.get('exe')
                        cwd = proc.info.get('cwd')
                        if exe and exe.upper().startswith(drive_path):
                            is_running = True
                            break
                        if cwd and cwd.upper().startswith(drive_path):
                            is_running = True
                            break
                        
                        # Vemos se algum outro `.exe` pertencente ao jogo foi gerado recentemente após iniciarmos este script
                        c_time = proc.info.get('create_time', 0)
                        if c_time >= script_start - 5:  # Margem segura
                            name = proc.info.get('name')
                            if name and name.lower() in game_exes:
                                is_running = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                        continue
                        
            if not is_running:
                log_output("Monitoramento detectou que o jogo e todos os seus subprocessos foram encerrados.")
                break
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        log_output("Interrupção do usuário recebida (CTRL+C). Forçando encerramento...")
        pass

def kill_ghost_exes(game_exes):
    """Fecha de forma forçada os executáveis do jogo caso tenham crashado por trás."""
    if game_exes:
        log_output(f"Mapeando e forçando limpeza da árvore de executáveis internos: {', '.join(game_exes)}")
    for exe_name in game_exes:
        kill_process_by_name(exe_name)

def main():
    hide_console()
    script_start = time.time()
    
    log_output("====== Iniciando Arcade Dump Launcher ======")
    
    # Executa a limpeza preventiva de velhas instâncias perdidas do sistema pyinstaller _MEI
    log_output("Preparando o ambiente e limpando vestígios anteriores...")
    clean_temp_files()

    if len(sys.argv) < 2:
        log_output("Falha: Caminho da ROM não foi fornecido para a execução.")
        sys.exit(1)

    rom_path = sys.argv[1]
    drive_root = f"{DRIVE_LETTER}:\\"

    # 1. Limpeza inicial rigorosa
    log_output("Certificando-se de que não existem instâncias antigas de mount travando o sistema...")
    kill_process_by_name("mount.exe")
    time.sleep(1)

    # 2. Montagem sem exibição de console
    log_output(f"Efetuando a montagem virtual (SquashFS/ZIP) da ROM: {rom_path}")
    try:
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
        else:
            creationflags = 0
        
        subprocess.Popen([MOUNT_EXE, rom_path, "-drive", DRIVE_LETTER], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=creationflags)
    except Exception as e:
        log_output(f"Erro ao tentar executar o mount.exe: {e}")
        sys.exit(1)

    # 3. Aguarda montagem
    if not wait_for_drive(drive_root):
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 4. Parâmetros de Launch
    log_output("Lendo e parseando o autorun.cmd do jogo...")
    config = get_autorun_params(drive_root)
    if not config or not config.get("CMD"):
        log_output("Falha ao ler o arquivo autorun.cmd, o jogo parece estar vazio ou incompatível.")
        kill_process_by_name("mount.exe")
        sys.exit(1)

    # 5. Execução do Jogo
    target_dir = os.path.normpath(os.path.join(drive_root, config.get("DIR", "")))
    game_cmd = config["CMD"]
    game_exe_path = os.path.join(target_dir, game_cmd)

    log_output(f"O comando definido foi localizado: {game_exe_path}")
    log_output("Iniciando injeção gráfica no ambiente do jogo...")

    try:
        # Iniciamos pela shell do sistema na target_dir correspondente
        process = subprocess.Popen(game_exe_path, cwd=target_dir, shell=True)
        
        # Estabilização dos subprocessos do emulador local
        time.sleep(5)
        
        # Rotina resiliente de espera avaliando todos executáveis possíveis da pasta
        wait_for_process_end(process, DRIVE_LETTER, target_dir, script_start)

    except Exception as e:
        log_output(f"Exceção durante a execução ou monitoramento do jogo: {e}")
        pass
    finally:
        log_output("====== Iniciando sequência de Desmontagem e Limpeza Final ======")
        # 6. Desmontagem e Limpeza final
        # Explicito forçar fechamento de qualquer exe do jogo que travou para não segurar o volume virtual
        kill_ghost_exes(get_game_exes(target_dir))
        time.sleep(1)
        
        # Elimina a unidade virtual de forma cirúrgica
        log_output("Desmontando o drive virtual Z:\\ via encerramento do mount...")
        kill_process_by_name("mount.exe")
        time.sleep(2)
        
        # Limpa os lixos temporários que acabaram de ser utilizados (caso force kill do pyinstaller local)
        log_output("Aplicando faxina final na lixeira do sistema...")
        clean_temp_files()
        
        log_output("====== Concluído com sucesso. Fechando Arcade Launcher ======")

if __name__ == "__main__":
    main()

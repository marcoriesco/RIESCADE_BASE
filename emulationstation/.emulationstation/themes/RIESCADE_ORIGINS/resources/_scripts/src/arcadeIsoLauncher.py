import os
import sys
import subprocess
import time
import shutil
import psutil
import tempfile
import ctypes
from pathlib import Path

def log_output(msg):
    try:
        print(f"[ArcadeISOLauncher] {msg}", flush=True)
    except Exception:
        pass

def hide_console():
    try:
        if os.name == 'nt':
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

def clean_temp_files():
    temp_dir = tempfile.gettempdir()
    try:
        for item in os.listdir(temp_dir):
            if item.startswith("_MEI"):
                mei_path = os.path.join(temp_dir, item)
                if os.path.isdir(mei_path):
                    try:
                        shutil.rmtree(mei_path)
                    except:
                        pass
    except:
        pass

def kill_process_by_name(process_name):
    log_output(f"Forçando o encerramento preventivo: {process_name}")
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(["taskkill", "/f", "/t", "/im", process_name], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=creationflags)
    except:
        pass

def mount_iso_and_get_drive(iso_path):
    """Monta a ISO nativamente no Windows via PowerShell Psh e retorna a letra vinculada a ela."""
    log_output(f"Solicitando montagem nativa da ISO no Kernel do Win10+ ({iso_path})...")
    ps_cmd = f"""
    try {{
        $ImagePath = '{iso_path}'
        Mount-DiskImage -ImagePath $ImagePath -ErrorAction SilentlyContinue | Out-Null
        $DiskImage = Get-DiskImage -ImagePath $ImagePath
        $Volume = $DiskImage | Get-Volume
        if ($Volume) {{
            Write-Output $Volume.DriveLetter
        }} else {{
            Start-Sleep -Milliseconds 600
            $Volume = Get-DiskImage -ImagePath $ImagePath | Get-Volume
            if ($Volume) {{ Write-Output $Volume.DriveLetter }}
        }}
    }} catch {{
        Write-Error $_
    }}
    """
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                                capture_output=True, text=True, creationflags=creationflags)
        
        linhas = [l.strip() for l in result.stdout.split('\n') if l.strip()]
        if linhas:
            drive_letter = linhas[-1]  # Última print é a letra: E, F...
            if len(drive_letter) == 1 and drive_letter.isalpha():
                log_output(f"Sucesso! Imagem montada perfeitamente no drive: [{drive_letter}:\\]")
                return drive_letter
                
        log_output(f"ALERTA: O Powershell falhou em reportar uma letra. Log Erro: {result.stderr.strip()}")
    except Exception as e:
        log_output(f"Erro Crítico de PowerShell durante o Mounting: {e}")
    return None

def unmount_iso(iso_path):
    """Desmonta a ISO mapeada e apaga o volume virtual."""
    log_output("Invocando desmontagem de Volume Virtual e liberação da Imagem ISO...")
    ps_cmd = f"""
    $ImagePath = '{iso_path}'
    Dismount-DiskImage -ImagePath $ImagePath | Out-Null
    """
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                       creationflags=creationflags)
    except:
        pass

def get_autorun_params(drive_root):
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
    exes = set()
    try:
        for path in Path(target_dir).glob("*.exe"):
            exes.add(path.name.lower())
    except:
        pass
    generic_exes = {"cmd.exe", "conhost.exe", "timeout.exe", "taskkill.exe", "ping.exe", "choice.exe"}
    return exes - generic_exes

def wait_for_process_end(process, drive_letter, target_dir, script_start):
    game_exes = get_game_exes(target_dir)
    drive_path = f"{drive_letter}:\\".upper()
    log_output("Jogo iniciado! Motor de checagem contra ghosting e runners bloqueando o Disco engatilhado...")
    
    try:
        while True:
            is_running = False
            
            if process.poll() is None:
                is_running = True
                
            if not is_running:
                for proc in psutil.process_iter(['name', 'exe', 'cwd', 'create_time']):
                    try:
                        exe = proc.info.get('exe')
                        cwd = proc.info.get('cwd')
                        if exe and exe.upper().startswith(drive_path):
                            is_running = True
                            break
                        if cwd and cwd.upper().startswith(drive_path):
                            is_running = True
                            break
                        
                        c_time = proc.info.get('create_time', 0)
                        if c_time >= script_start - 5:
                            name = proc.info.get('name')
                            if name and name.lower() in game_exes:
                                is_running = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                        continue
                        
            if not is_running:
                log_output("O sistema reportou que todas os fios/processos do jogo chegaram ao fim.")
                break
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        pass

def kill_ghost_exes(game_exes):
    if game_exes:
        log_output(f"Mapeando subexe's pra desengatar volume virtual limpo: {', '.join(game_exes)}")
    for exe_name in game_exes:
        kill_process_by_name(exe_name)

def main():
    hide_console()
    script_start = time.time()
    
    log_output("====== Iniciando Arcade ISO Launcher (WinNative) ======")
    clean_temp_files()

    if len(sys.argv) < 2:
        log_output("Erro Crítico: Caminho da ISO ausente!")
        sys.exit(1)

    iso_path = os.path.abspath(sys.argv[1])
    
    # 1. Garante que se o usuário forçou restart da lixeira sem Eject e a ISO tá block, a gnt desmonta preventivamente
    unmount_iso(iso_path)
    time.sleep(1)

    # 2. Montar a ISO e descobrir que letra o Windows dinamicamente nos deu
    drive_letter = mount_iso_and_get_drive(iso_path)
    if not drive_letter:
        log_output("Não conseguimos extrair a letra do Drive do PowerShell, impossível continuar.")
        sys.exit(1)

    drive_root = f"{drive_letter}:\\"

    # 3. Ler parâmetros contidos no autorun (Lê nativamente sem latência)
    log_output(f"Acessando sistema de leitura interna em {drive_root} ...")
    config = get_autorun_params(drive_root)
    if not config or not config.get("CMD"):
        log_output("Faltando autorun.cmd ou configurável falhou em apontar roteamento interno.")
        unmount_iso(iso_path)
        sys.exit(1)

    target_dir = os.path.normpath(os.path.join(drive_root, config.get("DIR", "")))
    game_cmd = config["CMD"]
    game_exe_path = os.path.join(target_dir, game_cmd)
    
    log_output(f"Start command computado e referenciado: {game_exe_path}")

    try:
        # Abertura primária
        process = subprocess.Popen(game_exe_path, cwd=target_dir, shell=True)
        time.sleep(5)
        
        # Rotina hipervigilante de processos (Herança)
        wait_for_process_end(process, drive_letter, target_dir, script_start)

    except Exception as e:
        log_output(f"Crash reportado pelo subprocess ao rodar o Jogo: {e}")
        pass
    finally:
        log_output("====== Terminando Seção Jogo. Inciando rotina de limpeza final ======")
        kill_ghost_exes(get_game_exes(target_dir))
        time.sleep(1)
        
        unmount_iso(iso_path)
        time.sleep(2)
        
        clean_temp_files()
        log_output("====== Arcade ISO Launcher Encerrado! ======")

if __name__ == "__main__":
    main()

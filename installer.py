import os
import sys
import subprocess
import shutil
from pathlib import Path
import ctypes

# Configuration
CONFIG = {
    "install_dir": Path("C:/ConnecteurBuffer"),
    "db_name": "connecteur_buffer",
    "db_user": "connecteur_user",
    "db_password": "Connecteur123!",  # À changer
    "app_dir": Path("app")
}

def run_as_admin():
    """Redémarre en admin si nécessaire"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def install_postgres():
    """Installe PostgreSQL depuis install_assets"""
    print("\n[1/4] Installation de PostgreSQL...")
    postgres_installer = Path("install_assets/postgresql-17-windows-x64.exe")
    
    cmd = [
        str(postgres_installer),
        "--mode unattended",
        "--unattendedmodeui minimal",
        f"--superpassword {CONFIG['db_password']}",
        "--enable-components commandlinetools",
        "--disable-components stackbuilder,pgAdmin4",
        "--servicename postgresql17",
        f"--servicepassword {CONFIG['db_password']}",
        "--serverport 5432",
        f"--prefix {CONFIG['install_dir'] / 'PostgreSQL'}"
    ]
    subprocess.run(" ".join(cmd), shell=True, check=True)
    
    # Ajout au PATH
    pg_bin = CONFIG["install_dir"] / "PostgreSQL/bin"
    os.environ["PATH"] = f"{pg_bin};{os.environ['PATH']}"

def setup_python():
    """Configure Python embarqué"""
    print("\n[2/4] Configuration de Python...")
    python_dir = CONFIG["install_dir"] / "Python"
    shutil.copytree("install_assets/python-embed", python_dir)
    
    # Configurer python._pth
    (python_dir / "python._pth").write_text("python311.zip\n.\nLib\\site-packages\n")
    os.environ["PATH"] = f"{python_dir};{os.environ['PATH']}"

def init_database():
    """Initialise la base de données"""
    print("\n[3/4] Initialisation de la base...")
    subprocess.run(f'psql -U postgres -c "CREATE DATABASE {CONFIG["db_name"]};"', shell=True, check=True)
    subprocess.run(f'psql -U postgres -d {CONFIG["db_name"]} -f "install_assets/initdb.sql"', shell=True, check=True)
    subprocess.run(f'psql -U postgres -c "CREATE USER {CONFIG["db_user"]} WITH PASSWORD \'{CONFIG["db_password"]}\';"', shell=True, check=True)
    subprocess.run(f'psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE {CONFIG["db_name"]} TO {CONFIG["db_user"]};"', shell=True, check=True)

def install_requirements():
    """Installe les dépendances Python"""
    print("\n[4/4] Installation des dépendances...")
    python_exe = CONFIG["install_dir"] / "Python/python.exe"
    requirements = CONFIG["app_dir"] / "requirements.txt"
    subprocess.run(f'"{python_exe}" -m pip install -r "{requirements}"', shell=True, check=True)

def deploy_app():
    """Déploie l'application"""
    print("\nDéploiement de l'application...")
    target_dir = CONFIG["install_dir"] / "app"
    shutil.copytree(CONFIG["app_dir"], target_dir)

def create_start_script():
    """Crée un script de démarrage"""
    content = f"""@echo off
set PATH=%~dp0Python;%PATH%
"%~dp0Python\\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
"""
    (CONFIG["install_dir"] / "start_app.bat").write_text(content)

def create_shortcut():
    """Crée un raccourci sur le bureau"""
    desktop = Path.home() / "Desktop"
    shortcut = desktop / "Connecteur Buffer.lnk"
    
    from win32com.client import Dispatch
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(str(shortcut))
    shortcut.TargetPath = str(CONFIG["install_dir"] / "start_app.bat")
    shortcut.WorkingDirectory = str(CONFIG["install_dir"])
    shortcut.IconLocation = str(CONFIG["install_dir"] / "app/static/evidence.ico")
    shortcut.save()

def main():
    run_as_admin()
    CONFIG["install_dir"].mkdir(exist_ok=True)
    
    try:
        install_postgres()
        setup_python()
        init_database()
        deploy_app()
        install_requirements()
        create_start_script()
        create_shortcut()
        
        print("\nInstallation terminée avec succès!")
        print(f"Raccourci créé sur le bureau")
        print(f"Installé dans: {CONFIG['install_dir']}")
        input("Appuyez sur Entrée pour quitter...")
        
    except Exception as e:
        print(f"\nERREUR: {str(e)}")
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)

if __name__ == "__main__":
    main()
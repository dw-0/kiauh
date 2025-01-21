import os
import subprocess

def install_droidklipp():
    try:
        print("Installing DroidKlipp...")
        subprocess.run(['sudo', 'apt', 'install', '-y', 'adb', 'tmux'], check=True)

        droidklipp_repo_url = "https://github.com/CodeMasterCody3D/DroidKlipp.git"
        if not os.path.isdir('DroidKlipp'):
            subprocess.run(['git', 'clone', droidklipp_repo_url], check=True)

        os.chdir('DroidKlipp')
        subprocess.run(['sudo', 'chmod', '+x', 'droidklipp.sh'], check=True)
        subprocess.run(['./droidklipp.sh'], check=True)

        print("DroidKlipp installation complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

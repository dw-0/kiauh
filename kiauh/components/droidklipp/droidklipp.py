import os
import subprocess

def install_droidklipp():
    try:
        print("Installing DroidKlipp...")

        # Install necessary dependencies
        subprocess.run(['sudo', 'apt', 'install', '-y', 'adb', 'tmux'], check=True)

        # Define the DroidKlipp repository URL and directory
        droidklipp_repo_url = "https://github.com/CodeMasterCody3D/DroidKlipp.git"
        droidklipp_dir = os.path.expanduser('~/DroidKlipp')

        # Check if DroidKlipp directory exists, if not create it
        if not os.path.isdir(droidklipp_dir):
            print("DroidKlipp folder not found, creating directory...")
            os.makedirs(droidklipp_dir)

        # Clone the repository if not already cloned
        if not os.path.isdir(os.path.join(droidklipp_dir, '.git')):
            print("Cloning the DroidKlipp repository...")
            subprocess.run(['git', 'clone', droidklipp_repo_url, droidklipp_dir], check=True)
        else:
            print("DroidKlipp repository already exists.")

        # Change to the DroidKlipp directory
        os.chdir(droidklipp_dir)

        # Set executable permissions for the installation script
        subprocess.run(['sudo', 'chmod', '+x', 'droidklipp.sh'], check=True)

        # Run the installation script
        subprocess.run(['./droidklipp.sh'], check=True)

        print("DroidKlipp installation complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Run the function
install_droidklipp()

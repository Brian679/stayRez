# Android Build Instructions

This guide explains how to convert the **offRez** Kivy application into an Android APK using [Buildozer](https://github.com/kivy/buildozer).

**Note:** Buildozer natively runs on Linux. To build on Windows, you must use **WSL 2 (Windows Subsystem for Linux)**.

## Prerequisites

1.  **Enable WSL 2** on your Windows machine:
    Open PowerShell as Administrator and run:
    ```powershell
    wsl --install
    ```
    (Reboot your computer if prompted).

2.  **Open your project in WSL**:
    - Open the "Ubuntu" terminal app.
    - Navigate to your project folder.
      (e.g., `cd /mnt/c/Users/USER/stayRez/mobile/kivy_app`)

3.  **Install Build Dependencies (in Ubuntu terminal)**:
    Update your package lists and install necessary system tools:
    ```bash
    sudo apt update
    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
    ```
    *(Note: Java 17 is generally recommended for recent Android builds.)*

4.  **Install Buildozer**:
    ```bash
    pip3 install --user --upgrade buildozer
    # Ensure local bin is in PATH
    export PATH=$PATH:~/.local/bin
    ```

## Building the APK

1.  **Navigate to the app directory**:
    Ensure you are inside `mobile/kivy_app`:
    ```bash
    cd mobile/kivy_app
    ```

2.  **Initialize Buildozer (Skipped)**:
    We have already created the `buildozer.spec` file for you.

3.  **Start the Build**:
    Run the following command to build the debug APK:
    ```bash
    buildozer android debug
    ```
    *This process will take a significant amount of time (15-60 mins) on the first run as it downloads the Android SDK, NDK, and compiles python for android.*

4.  **Deploy to Device (Optional)**:
    If you have an Android device connected via USB (with USB Debugging enabled):
    ```bash
    buildozer android deploy run
    ```

## Important Settings

- **API URL**:
  Currently, `main.py` is configured to point to **`https://www.offrezapp.co.zw/api/`** (Production).
  - If you need to test locally:
    - Android Emulator: `http://10.0.2.2:8000/api/`
    - Physical Device: Your PC's IP (e.g., `http://192.168.1.5:8000/api/`)
  - Update the `API_BASE` variable in `main.py` if you want to switch back to local testing.

- **Dependencies**:
  The `buildozer.spec` file (`requirements` line) must list all Python packages your app uses. Currently set to: `python3,kivy,pillow,certifi`.

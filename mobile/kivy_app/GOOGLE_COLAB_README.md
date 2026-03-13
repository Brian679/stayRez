# Build with Google Colab (No WSL Required)

If WSL is not working on your machine, you can build the APK using **Google Colab**. This runs the build on a remote Google server.

## Steps

1.  **Prepare your files**:
    *   Navigate to the `mobile` folder in your file explorer.
    *   Right-click the `kivy_app` folder and select **Send to > Compressed (zipped) folder**.
    *   Rename the resulting file to **`kivy_app.zip`**.

2.  **Open Google Colab**:
    *   Go to [https://colab.research.google.com/](https://colab.research.google.com/)
    *   Click **New Notebook**.

3.  **Setup the Build Environment**:
    *   Copy and paste the following code into the first cell and run it (Shift+Enter). This cleans up old runs and handles the upload.

```python
import os
from google.colab import files
import shutil

# Clean up previous runs
if os.path.exists("kivy_app"):
    shutil.rmtree("kivy_app")
if os.path.exists("bin"):
    shutil.rmtree("bin")

# Upload the zip file
print("Please upload your kivy_app.zip file now...")
uploaded = files.upload()

# Unzip
for fn in uploaded.keys():
    print('User uploaded file "{name}" with length {length} bytes'.format(
        name=fn, length=len(uploaded[fn])))
    !unzip -q {fn}
    print("Unzipped!")
```

4.  **Install Buildozer**:
    *   Add a new code cell and run:

```python
!pip install buildozer cython==0.29.33

# Install system dependencies
!sudo apt-get update
!sudo apt-get install -y \
    python3-pip \
    build-essential \
    git \
    python3 \
    python3-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev

# Install GStreamer plugins
!sudo apt-get install -y libgstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good

# Install additional build tools (ensure automake/autoconf/libtool are present)
!sudo apt-get install -y \
    autoconf \
    libtool \
    pkg-config \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    zip \
    unzip \
    openjdk-17-jdk

# Ensure architecture is compatible (sometimes aidl needs libstdc++)
!sudo apt-get install -y libstdc++6
```

5.  **Run the Build**:
    *   Add a new code cell and run:
    *(Type 'y' in the output box if prompted for license agreement, though the config is set to auto-accept)*

```python
import os

# Robustly find the project folder by looking for buildozer.spec
target_dir = None
for root, dirs, files in os.walk("."):
    if "buildozer.spec" in files:
        target_dir = root
        break

if target_dir:
    print(f"Found project in: {target_dir}")
    os.chdir(target_dir)
    !buildozer android debug
else:
    print("Error: buildozer.spec not found. Did the zip file upload and unzip correctly?")
    print("Current directories:", os.listdir())
```

6.  **Download the APK**:
    *   Once the build steps finish (it will take 15-20 mins), run this cell to find and download your APK:

```python
from google.colab import files
import glob

apk_files = glob.glob("bin/*.apk")
if apk_files:
    files.download(apk_files[0])
    print("Downloading:", apk_files[0])
else:
    print("No APK found. Check the build logs above for errors.")
```

## Installing on Your Phone

1.  **Transfer the APK**: If you downloaded the file to your computer, transfer it to your Android phone (via USB, Google Drive, Email, or WhatsApp).
2.  **Allow Unknown Sources**: When you try to install the APK, your phone might warn you about installing from unknown sources.
    *   Go to **Settings > Security** (or search for "Unknown apps").
    *   Allow the installation for the app you are using to open the APK (e.g., File Manager, Chrome, Drive).
3.  **Install**: Follow the on-screen prompts to install **offRez**.
4.  **Run**: Open the app!

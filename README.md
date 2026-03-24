# Bookworm Adventures KeyCast
Keyboard support for Bookworm Adventures by PopCap Games with screencasting and template matching.

# Disclaimer
This just a personal project for my sake.

Hotkeys: 
- F9 = Scan
- F10: Start/Stop


## Install Requirements:
```
pip install -r requirements.txt
```

### GStream Dependency
System: GStreamer plugins (base, good), PipeWire

## Build Executable (PyInstaller)

Notes:
- Build on the target OS (build Windows `.exe` on Windows).
- Linux screencast uses DBus + GStreamer + PipeWire via PyGObject; those are system dependencies and usually are not fully bundled by PyInstaller.

### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --clean --onedir \
	--name keycast-bwa \
	--contents-directory . \
	--paths src \
	--add-data "app_config.json:." \
	--add-data "templates:templates" \
	src/main.py
```

### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --clean --onedir --windowed `
	--name keycast-bwa `
	--contents-directory . `
	--paths src `
	--add-data "app_config.json;." `
	--add-data "images;images" `
	--add-data "templates;templates" `
	src\main.py
```

## Example
![Example](/images/example.png)
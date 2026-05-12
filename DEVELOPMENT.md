# Development Guide: ComplianShift CLI

This guide covers how to set up a development environment and build the **ComplianShift CLI** as a standalone binary using PyInstaller.

## Prerequisites

- **Python 3.10** or higher
- **pip** (bundled with Python)
- Access to an OpenShift cluster for manual testing

## 1. Setting Up the Development Environment

Clone the repository and create a virtual environment:

```bash
git clone <repository-url>
cd ocp-tool

python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

To run the tool directly from source during development:

```bash
python main.py
```

## 2. Project Structure

```text
ocp-tool/
├── main.py                  # CLI entry point (Typer)
├── complianshift.spec       # PyInstaller build spec
├── mapping.yaml             # Operator name → Red Hat product name mapping
├── requirements.txt         # Runtime dependencies
├── data/                    # Runtime cache folder (API responses)
├── build/                   # PyInstaller build artifacts (generated)
├── dist/                    # Final binary output (generated)
├── core/
│   ├── k8s_client.py        # Kubernetes/OpenShift client logic
│   └── scanner.py           # Supportability scan and API v2 logic
└── ui/
    ├── formatter.py         # Rich tables and panels
    └── exporter.py          # HTML/Markdown report exporter
```

## 3. Building the Binary

ComplianShift uses [PyInstaller](https://pyinstaller.org) to produce a single self-contained executable that does not require Python to be installed on the target machine.

### 3.1 Install PyInstaller

PyInstaller is a build-time dependency and is not listed in `requirements.txt`. Install it in your virtual environment:

```bash
pip install pyinstaller
```

### 3.2 Run the Build

A pre-configured spec file (`complianshift.spec`) is provided at the root of the project. It handles all bundling rules, including embedding the `mapping.yaml` file and any pre-downloaded lifecycle data.

To build the binary:

```bash
pyinstaller complianshift.spec
```

The build output will be placed in:

```
dist/
└── complianshift      # Standalone executable
```

### 3.3 What the Spec File Does

The `complianshift.spec` file instructs PyInstaller to:

| Setting | Description |
|---|---|
| `Analysis(['main.py'])` | Uses `main.py` as the entry point |
| `datas` | Bundles `mapping.yaml` and any pre-fetched lifecycle JSON files from `data/` into the binary |
| `name='complianshift'` | Names the output binary `complianshift` |
| `upx=True` | Compresses the binary with UPX if available (reduces file size) |
| Single-file mode | `a.scripts`, `a.binaries`, `a.datas` are all passed to `EXE`, producing one file |

### 3.4 Updating Bundled Data Files

The spec file has a `datas` list that maps local files into the binary. If you need to bundle additional pre-downloaded lifecycle JSON files, edit `complianshift.spec` and add entries to the `datas` list:

```python
datas=[
    ('mapping.yaml', '.'),
    ('data/product_lifecycle_data_ocp_418.json', 'data/'),
    ('data/product_lifecycle_data_ocp_420.json', 'data/'),
    ('data/product_lifecycle_data_ocp_421.json', 'data/'),
    # Add new versions here, e.g.:
    # ('data/product_lifecycle_data_ocp_422.json', 'data/'),
],
```

Then re-run `pyinstaller complianshift.spec` to rebuild.

## 4. Making the Binary Available System-Wide

After building, you can copy the binary to a directory in your `PATH` so it can be called from anywhere:

```bash
# Linux/macOS
sudo cp dist/complianshift /usr/local/bin/complianshift
sudo chmod +x /usr/local/bin/complianshift

# Or for the current user only (no sudo required)
cp dist/complianshift ~/.local/bin/complianshift
```

Verify the installation:

```bash
complianshift --help
```

## 5. Cleaning Build Artifacts

To start a clean build, remove the `build/` and `dist/` directories:

```bash
rm -rf build/ dist/
pyinstaller complianshift.spec
```

## 6. Dependency Management

Runtime dependencies are declared in `requirements.txt`:

| Package | Purpose |
|---|---|
| `rich` | Terminal tables, panels, and progress spinners |
| `typer` | CLI argument and command parsing |
| `kubernetes` | Kubernetes/OpenShift API client |
| `requests` | HTTP calls to the Red Hat Product Lifecycle API |
| `PyYAML` | Parsing `mapping.yaml` |

To add a new dependency:

```bash
pip install <package>
pip freeze | grep <package> >> requirements.txt
```

## 7. Running Tests and Linting

> This section should be updated as the project gains a test suite and linting configuration.

For now, run the tool end-to-end against a real cluster to validate changes:

```bash
python main.py --debug
```

# Usage Guide: ComplianShift CLI

This guide explains how to install, configure, and run the **ComplianShift CLI** in your environment.

## 1. Installation

ComplianShift can be run in two ways: directly from source (requires Python) or as a pre-built standalone binary (no Python required). Choose the method that fits your environment.

### Option A — Run from Source (Python required)

Ensure you have Python 3.10+ installed. Then install the dependencies listed in `requirements.txt`:

```bash
# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Option B — Run the Pre-built Binary (no Python required)

Download or build the `complianshift` binary (see [DEVELOPMENT.md](DEVELOPMENT.md)) and optionally install it system-wide:

```bash
# Make the binary executable (if not already)
chmod +x ./complianshift

# Optional: install it to PATH so you can call it from anywhere
sudo cp ./complianshift /usr/local/bin/complianshift
```

## 2. Authentication on the Cluster

The tool uses the current context of your Kubernetes/OpenShift. Ensure you are logged into the target cluster:

```bash
oc login --token=YOUR_TOKEN --server=CLUSTER_URL
# or ensure the KUBECONFIG variable points to a valid file
```

## 3. Execution

The CLI was built using the `Typer` library. The commands are identical whether you are running from source or using the compiled binary — just replace `python main.py` with `complianshift` (or `./complianshift` if the binary is not on your `PATH`).

### Running from Source

```bash
python main.py
```

### Running the Compiled Binary

```bash
# If the binary is on your PATH
complianshift

# If running from the dist/ directory
./complianshift
```

### Available Flags

You can run with additional flags to control the cache and detail level:

```bash
# Force ignoring the cache and download everything again
complianshift --force

# Change cache validity time (default is 30 min)
complianshift --cache-minutes 60

# Display detailed logs of what is happening under the hood
complianshift --debug

# Export the compliance table to HTML
complianshift -o html

# Export to Markdown in a specific directory
complianshift -o md -p ./reports

# Combine with other flags
complianshift --force -o html -p /tmp/reports
```

You can also view the built-in help by running:

```bash
complianshift --help
```

### What to expect from the execution:
1. A *spinner* will indicate that the tool is querying the Red Hat API and the cluster.
2. The tool will display the individual progress of each operator.
3. At the end, a consolidated table will be displayed.
4. If there are operators out of the support window (EOL), a red alert panel will be displayed at the end, recommending an upgrade.
5. If `--output` is specified, a report file (`compliance-report-YYYY-MM-DD.html` or `.md`) will be generated in the directory specified by `--path` (defaults to the current directory).

## 4. Cache Management

To optimize queries and avoid API blocks, ComplianShift stores data in a local cache within the `data/` folder.
The generated files are:
- `data/product-lifecycle.json` (Red Hat API v2 data)
- `data/csvs-report.json` (Cached cluster CSVs)

The cache is valid for 30 minutes by default. You can force an update using the `--force` flag in the scan command, or simply by deleting the files from the `data/` folder.

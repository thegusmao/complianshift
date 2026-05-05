# Usage Guide: ComplianShift CLI

This guide explains how to install, configure, and run the **ComplianShift CLI** in your environment.

## 1. Installation

First, ensure you have Python 3.10+ installed. Then, install the dependencies listed in the `requirements.txt` file:

```bash
# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. Authentication on the Cluster

The tool uses the current context of your Kubernetes/OpenShift. Ensure you are logged into the target cluster:

```bash
oc login --token=YOUR_TOKEN --server=CLUSTER_URL
# or ensure the KUBECONFIG variable points to a valid file
```

## 3. Execution

The CLI was built using the `Typer` library. Running `python main.py` will execute the supportability scan:

```bash
python main.py
```

You can run with additional flags to control the cache and detail level:
```bash
# Force ignoring the cache and download everything again
python main.py --force

# Change cache validity time (default is 30 min)
python main.py --cache-minutes 60

# Display detailed logs of what is happening under the hood
python main.py --debug
```

You can also view the built-in help by running:
```bash
python main.py --help
```

### What to expect from the execution:
1. A *spinner* will indicate that the tool is querying the Red Hat API and the cluster.
2. The tool will display the individual progress of each operator.
3. At the end, a consolidated table will be displayed.
4. If there are operators out of the support window (EOL), a red alert panel will be displayed at the end, recommending an upgrade.

## 4. Cache Management

To optimize queries and avoid API blocks, ComplianShift stores data in a local cache within the `data/` folder.
The generated files are:
- `data/product-lifecycle.json` (Red Hat API v2 data)
- `data/csvs-report.json` (Cached cluster CSVs)

The cache is valid for 30 minutes by default. You can force an update using the `--force` flag in the scan command, or simply by deleting the files from the `data/` folder.

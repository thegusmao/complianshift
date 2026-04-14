import re
import json
import time
import requests
from pathlib import Path


class Scanner:
    def __init__(self, k8s_client, mapping_file="mapping.yaml", data_dir="data"):
        self.k8s = k8s_client
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.data_dir / "product-lifecycle.json"

        import yaml
        try:
            with open(mapping_file, "r") as f:
                raw = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raw = {}

        self.version_override = raw.pop("version_override", {})
        self.mapping = raw

    # ── cache helpers ──────────────────────────────────────────────

    def _is_cache_valid(self, file_path, cache_minutes, force):
        if force or not file_path.exists():
            return False
        age_minutes = (time.time() - file_path.stat().st_mtime) / 60
        return age_minutes < cache_minutes

    # ── lifecycle data download ────────────────────────────────────

    def download_lifecycle_data(self, cache_minutes=30, force=False, console=None, debug=False):
        if self._is_cache_valid(self.json_path, cache_minutes, force):
            if console:
                console.print(f"[dim]Using local cache for lifecycle data (valid for {cache_minutes} min).[/dim]")
            return

        url = "https://access.redhat.com/product-life-cycles/api/v2/products"
        new_path = self.json_path.with_suffix(".json.new")
        old_path = self.json_path.with_suffix(".json.old")

        if console:
            console.print(f"[dim]Downloading lifecycle data from API v2: {url}[/dim]")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            with open(new_path, "w") as f:
                json.dump(data, f)

            if self.json_path.exists():
                if old_path.exists():
                    old_path.unlink()
                self.json_path.rename(old_path)

            new_path.rename(self.json_path)

            if console and debug:
                console.print(f"[dim]Download completed successfully. File saved at {self.json_path}[/dim]")

        except Exception as e:
            if console:
                console.print(f"[yellow]Warning: Failed to download API v2 data ({e}). Trying to use local file if it exists.[/yellow]")
            if not self.json_path.exists():
                raise RuntimeError("Could not download data and there is no local cache.")

    def load_lifecycle_data(self):
        with open(self.json_path, "r") as f:
            return json.load(f).get("data", [])

    # ── cluster queries ────────────────────────────────────────────

    def _get_current_ocp_version(self, console):
        if console:
            console.print("[dim]Fetching OpenShift version from the cluster...[/dim]")

        current_ocp_version = self.k8s.get_ocp_version()
        if current_ocp_version == "Unknown":
            if console:
                console.print("[yellow]Warning: Could not determine OpenShift version.[/yellow]")
            return current_ocp_version

        parts = current_ocp_version.split(".")
        if len(parts) >= 2:
            current_ocp_version = f"{parts[0]}.{parts[1]}"

        if console:
            console.print(f"[dim]Detected OpenShift version: {current_ocp_version}[/dim]")
        return current_ocp_version

    def _get_subscriptions(self, cache_minutes, force, console, debug):
        cache_path = self.data_dir / "subscriptions-report.json"
        if self._is_cache_valid(cache_path, cache_minutes, force):
            if console:
                console.print(f"[dim]Loading subscriptions from local cache ({cache_path})...[/dim]")
            with open(cache_path, "r") as f:
                return json.load(f)

        if console:
            console.print("[dim]Fetching Red Hat Operator Subscriptions from the cluster...[/dim]")

        subs = self.k8s.get_redhat_subscriptions(console=console, debug=debug)

        with open(cache_path, "w") as f:
            json.dump(subs, f, indent=2)
        if console and debug:
            console.print(f"[dim]Subscriptions saved to cache: {cache_path}[/dim]")

        return subs

    # ── version resolution ─────────────────────────────────────────

    _CHANNEL_VERSION_RE = re.compile(r"[\w-]*?-?v?(\d+[\.\d]*(?:\.x)?)$")

    def _extract_product_version(self, package, channel, operator_version):
        """Resolves the product version to use for lifecycle matching.
        Priority: 1) version_override  2) channel name regex  3) operator version."""
        overrides = self.version_override.get(package, {})
        if isinstance(overrides, dict) and channel in overrides:
            return str(overrides[channel])

        m = self._CHANNEL_VERSION_RE.match(channel)
        if m:
            return m.group(1)

        return operator_version

    # ── lifecycle matching ─────────────────────────────────────────

    def _resolve_api_name(self, package):
        return self.mapping.get(package, package)

    def _find_product_info(self, api_name, lifecycle_data):
        for p in lifecycle_data:
            if p.get("name") == api_name or api_name in p.get("former_names", []):
                return p
        return None

    def _find_matching_version(self, version_clean, versions, console, debug):
        v_parts = version_clean.split(".")
        minor_v = ".".join(v_parts[:2]) if len(v_parts) >= 2 else version_clean
        major_v = v_parts[0] if v_parts else version_clean

        search_patterns = [
            minor_v,
            f"{minor_v}.x",
            f"{major_v}.x",
            major_v,
        ]

        for pattern in search_patterns:
            for v in versions:
                if v.get("name", "") == pattern:
                    if console and debug:
                        console.print(f"[dim]  -> Match found using exact pattern: '{pattern}'[/dim]")
                    return v

        for v in versions:
            v_name = v.get("name", "")
            if v_name.startswith(f"{major_v}."):
                if console and debug:
                    console.print(f"[dim]  -> Partial match found (fallback to closest major version): '{v_name}'[/dim]")
                return v

        return None

    def _extract_end_date(self, matched_version, support_status):
        phases = matched_version.get("phases", [])
        for phase in phases:
            if phase.get("name", "").lower() == support_status.lower():
                end_date_raw = phase.get("end_date")
                if end_date_raw and end_date_raw != "N/A":
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(end_date_raw[:10], "%Y-%m-%d")
                        return dt.strftime("%d/%m/%Y")
                    except Exception:
                        return end_date_raw
        return "N/A"

    def _check_compatibility(self, matched_version, current_ocp_version):
        compat_str = matched_version.get("openshift_compatibility")
        if not compat_str or str(compat_str).strip() == "N/A" or current_ocp_version == "Unknown":
            return "N/A"

        if isinstance(compat_str, list):
            compat_list = [str(c).strip() for c in compat_str]
        else:
            compat_list = [c.strip() for c in str(compat_str).split(",")]

        return "Yes" if current_ocp_version in compat_list else "No"

    # ── result builder ─────────────────────────────────────────────

    def _build_result(self, sub, product_version, compat, status, end_date):
        return {
            "name": sub["package"],
            "scope": sub["scope"],
            "namespace": sub["namespace"],
            "channel": sub["channel"],
            "operator_version": sub["operator_version"],
            "product_version": product_version,
            "ocp_compatible": compat,
            "support_status": status,
            "end_date": end_date,
        }

    # ── main scan entry point ──────────────────────────────────────

    def scan_operators(self, cache_minutes=30, force=False, console=None, debug=False):
        current_ocp_version = self._get_current_ocp_version(console)
        subs = self._get_subscriptions(cache_minutes, force, console, debug)
        lifecycle_data = self.load_lifecycle_data()

        if console:
            console.print(f"[dim]Found {len(subs)} Red Hat subscriptions.[/dim]")

        results = []

        for sub in subs:
            package = sub["package"]
            channel = sub["channel"]
            operator_version = sub["operator_version"]

            if console:
                console.print(f"\n[bold cyan]Analyzing operator:[/bold cyan] {package}")

            product_version = self._extract_product_version(package, channel, operator_version)
            version_clean = product_version[1:] if product_version.startswith("v") else product_version

            api_name = self._resolve_api_name(package)
            if console and debug:
                console.print(
                    f"[dim]Looking for product: '{api_name}' "
                    f"(operator={operator_version}, product={product_version}, channel={channel})[/dim]"
                )

            product_info = self._find_product_info(api_name, lifecycle_data)
            if not product_info:
                if console:
                    console.print(f"[yellow]Product '{api_name}' not found in lifecycle data.[/yellow]")
                results.append(self._build_result(sub, product_version, "N/A", "Unknown", "N/A"))
                continue

            matched_version = self._find_matching_version(
                version_clean, product_info.get("versions", []), console, debug
            )
            if not matched_version:
                if console:
                    console.print(
                        f"[yellow]Compatible version for '{product_version}' not found for '{api_name}'.[/yellow]"
                    )
                results.append(self._build_result(sub, product_version, "N/A", "Version not found", "N/A"))
                continue

            support_status = matched_version.get("type", "Unknown")
            end_date = self._extract_end_date(matched_version, support_status)
            ocp_compatible = self._check_compatibility(matched_version, current_ocp_version)

            if console and debug:
                console.print(f"[dim]Status: {support_status}, EOL: {end_date}, OCP Compatible: {ocp_compatible}[/dim]")

            results.append(self._build_result(sub, product_version, ocp_compatible, support_status, end_date))

        return results

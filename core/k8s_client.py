from kubernetes import client, config


class K8sClient:
    def __init__(self):
        try:
            config.load_kube_config()
            self.api = client.CustomObjectsApi()
        except Exception as e:
            raise RuntimeError(f"Error loading ~/.kube/config: {e}")

    def get_ocp_version(self):
        """Fetches the current OpenShift version in the cluster."""
        try:
            cluster_version = self.api.get_cluster_custom_object(
                group="config.openshift.io",
                version="v1",
                plural="clusterversions",
                name="version"
            )
            history = cluster_version.get("status", {}).get("history", [])
            for entry in history:
                if entry.get("state") == "Completed":
                    return entry.get("version")
            return "Unknown"
        except Exception:
            return None

    def _extract_operator_version(self, installed_csv, package):
        """Extracts the operator version from the installedCSV field.
        E.g. '3scale-operator.v0.13.2' -> '0.13.2'"""
        if not installed_csv:
            return "N/A"
        if ".v" in installed_csv:
            return installed_csv.split(".v", 1)[1]
        prefix = f"{package}."
        if installed_csv.startswith(prefix):
            return installed_csv[len(prefix):]
        return installed_csv

    def _parse_subscription_item(self, sub):
        """Filters and converts a raw Subscription into a simplified dictionary."""
        spec = sub.get("spec", {})
        source = spec.get("source", "")

        if source != "redhat-operators":
            return None

        metadata = sub.get("metadata", {})
        status = sub.get("status", {})
        namespace = metadata.get("namespace", "")
        package = spec.get("name", metadata.get("name", ""))
        channel = spec.get("channel", "N/A")
        installed_csv = status.get("installedCSV") or status.get("currentCSV") or ""
        operator_version = self._extract_operator_version(installed_csv, package)
        scope = "Cluster" if namespace == "openshift-operators" else "Namespace"

        return {
            "package": package,
            "namespace": namespace,
            "channel": channel,
            "installed_csv": installed_csv,
            "operator_version": operator_version,
            "source": source,
            "scope": scope,
        }

    def get_redhat_subscriptions(self, console=None, debug=False):
        """Fetches Subscriptions across all namespaces and filters by source 'redhat-operators'.
        Uses pagination to handle large clusters."""
        try:
            if console and debug:
                console.print("[dim]Starting Kubernetes API call to list subscriptions (with pagination)...[/dim]")

            rh_subs = []
            limit = 200
            continue_token = None
            page_count = 1
            total_items = 0

            while True:
                if console and debug:
                    console.print(f"[dim]  -> Fetching page {page_count}...[/dim]")

                kwargs = {
                    "group": "operators.coreos.com",
                    "version": "v1alpha1",
                    "plural": "subscriptions",
                    "limit": limit,
                    "_request_timeout": 60,
                }
                if continue_token:
                    kwargs["_continue"] = continue_token

                subs_obj = self.api.list_cluster_custom_object(**kwargs)
                items = subs_obj.get("items", [])
                total_items += len(items)

                if console and debug:
                    console.print(f"[dim]  -> Page {page_count} returned {len(items)} items. Filtering...[/dim]")

                for sub in items:
                    parsed = self._parse_subscription_item(sub)
                    if parsed:
                        if console and debug:
                            console.print(
                                f"[dim]    - Found: {parsed['package']} "
                                f"(channel={parsed['channel']}) in {parsed['namespace']}[/dim]"
                            )
                        rh_subs.append(parsed)

                continue_token = subs_obj.get("metadata", {}).get("continue")
                if not continue_token:
                    break
                page_count += 1

            if console and debug:
                console.print(
                    f"[dim]Pagination complete. {total_items} subscriptions processed. "
                    f"Kept {len(rh_subs)} Red Hat subscriptions.[/dim]"
                )

            return rh_subs
        except Exception as e:
            raise RuntimeError(f"Error fetching Subscriptions: {e}")

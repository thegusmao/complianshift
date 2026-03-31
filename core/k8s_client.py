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
            return "Desconhecida"
        except Exception as e:
            # In case of error (e.g. not an OpenShift cluster, no permission), return None or log the error
            return None

    def _extract_package_name(self, metadata, name, namespace):
        """Tries to extract package name from labels or fallbacks to name."""
        labels = metadata.get("labels", {})
        for label in labels.keys():
            if label.startswith("operators.coreos.com/"):
                label_value = label.split("/")[1]
                if label_value.endswith(f".{namespace}"):
                    return label_value[:-(len(namespace)+1)]
        return name.split(".v")[0] if ".v" in name else name

    def _parse_csv_item(self, csv):
        """Filters and converts a raw CSV item into a simplified dictionary."""
        spec = csv.get("spec", {})
        provider = spec.get("provider", {})
        provider_name = provider.get("name", "") if isinstance(provider, dict) else provider
        
        if provider_name != "Red Hat":
            return None
            
        metadata = csv.get("metadata", {})
        namespace = metadata.get("namespace", "")
        name = metadata.get("name", "")
        
        package = self._extract_package_name(metadata, name, namespace)
        scope = "Cluster" if namespace == "openshift-operators" else "Namespace"
        
        return {
            "name": name,
            "display_name": spec.get("displayName", package),
            "package": package,
            "namespace": namespace,
            "version": spec.get("version", "N/A"),
            "scope": scope
        }

    def get_redhat_csvs(self, console=None, debug=False):
        """Fetches ClusterServiceVersions (CSVs) in the cluster and filters by provider 'Red Hat'.
        Uses pagination to avoid timeouts on large clusters."""
        try:
            if console and debug:
                console.print("[dim]Starting Kubernetes API call to list clusterserviceversions (with pagination)...[/dim]")
                
            rh_csvs = []
            limit = 200
            continue_token = None
            page_count = 1
            total_items_processed = 0

            while True:
                if console and debug:
                    console.print(f"[dim]  -> Fetching page {page_count}...[/dim]")
                
                kwargs = {
                    "group": "operators.coreos.com",
                    "version": "v1alpha1",
                    "plural": "clusterserviceversions",
                    "limit": limit,
                    "_request_timeout": 60
                }
                if continue_token:
                    kwargs["_continue"] = continue_token

                csvs_obj = self.api.list_cluster_custom_object(**kwargs)
                items = csvs_obj.get("items", [])
                total_items_processed += len(items)
                
                if console and debug:
                    console.print(f"[dim]  -> Page {page_count} returned {len(items)} items. Filtering...[/dim]")
                    
                for csv in items:
                    parsed_csv = self._parse_csv_item(csv)
                    if parsed_csv:
                        if console and debug:
                            console.print(f"[dim]    - Found Red Hat CSV: {parsed_csv['name']} in namespace {parsed_csv['namespace']}[/dim]")
                        rh_csvs.append(parsed_csv)
                
                continue_token = csvs_obj.get("metadata", {}).get("continue")
                if not continue_token:
                    break
                page_count += 1
                    
            if console and debug:
                console.print(f"[dim]Pagination complete. Total of {total_items_processed} CSVs processed. Kept {len(rh_csvs)} Red Hat CSVs.[/dim]")
                
            return rh_csvs
        except Exception as e:
            raise RuntimeError(f"Error fetching ClusterServiceVersions: {e}")
            
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
        except Exception as e:
            # In case of error (e.g. not an OpenShift cluster, no permission), return None or log the error
            return None

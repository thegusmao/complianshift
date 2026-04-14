import json
from pathlib import Path

from core.paths import get_base_path


class UpgradeChecker:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else get_base_path() / "data"
        self.operator_data = self._load_data()

    def _load_data(self):
        """Loads and merges all lifecycle JSON files."""
        merged_data = {}
        
        # Fetches all product_lifecycle_data_ocp_*.json files
        for file_path in self.data_dir.glob("product_lifecycle_data_ocp_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        op_name = item.get("name")
                        channels = item.get("channel", {})
                        
                        if op_name not in merged_data:
                            merged_data[op_name] = {}
                            
                        # Merge OCP versions for this operator
                        for ocp_ver, channel_list in channels.items():
                            if ocp_ver not in merged_data[op_name]:
                                merged_data[op_name][ocp_ver] = channel_list
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                
        return merged_data

    def _parse_current_version(self, current_ocp_version):
        if not current_ocp_version or current_ocp_version == "Unknown":
            return None
        parts = current_ocp_version.split(".")
        return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else None

    def _get_future_versions(self, current_major_minor):
        all_ocp_versions = set()
        for op_data in self.operator_data.values():
            all_ocp_versions.update(op_data.keys())
            
        try:
            current_float = float(current_major_minor)
            return sorted([v for v in all_ocp_versions if float(v) > current_float], key=float)
        except ValueError:
            return []

    def _check_operator_channels(self, target_data, current_channel):
        available_channels = []
        channel_supported = False
        
        for ch_info in target_data:
            ch_name_raw = ch_info.get("channel", "")
            
            display_channel = ch_name_raw.replace(" (default)", "").strip()
            available_channels.append(display_channel)
            
            base_channel_json = ch_name_raw.split(" ")[0]
            if base_channel_json == current_channel:
                channel_supported = True
                break
                
        return channel_supported, available_channels

    def check_upgrades(self, current_ocp_version, subscriptions):
        """
        Checks for each subsequent OCP version which operators need a channel upgrade.
        """
        current_major_minor = self._parse_current_version(current_ocp_version)
        if not current_major_minor:
            return {}
            
        future_versions = self._get_future_versions(current_major_minor)
        results = {}
        
        for target_version in future_versions:
            results[target_version] = []
            
            for sub in subscriptions:
                op_name = sub["package"]
                current_channel = sub["channel"]
                
                if op_name not in self.operator_data:
                    continue
                    
                target_data = self.operator_data[op_name].get(target_version, [])
                channel_supported, available_channels = self._check_operator_channels(target_data, current_channel)
                
                if not channel_supported and available_channels:
                    results[target_version].append({
                        "operator": op_name,
                        "current_channel": current_channel,
                        "recommended_channels": available_channels
                    })
                    
        return results

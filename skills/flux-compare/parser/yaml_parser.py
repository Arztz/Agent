#!/usr/bin/env python3
"""
YAML Parser for Flux Compare skill.
Parses patch.yaml (HelmRelease) and secrets.yaml (Secret) files.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ResourceData:
    """Parsed resource data from patch.yaml"""
    service_name: str
    replica_count: Optional[int] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    cpu_request: Optional[str] = None
    memory_request: Optional[str] = None
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None
    autoscaling_enabled: bool = False


@dataclass
class EnvData:
    """Parsed ENV data from secrets.yaml"""
    service_name: str
    default_keys: List[str]  # First 6 fixed keys
    sorted_keys: List[str]   # Alphabetically sorted keys after separator
    raw_keys: List[str]      # All keys in original order
    
    @property
    def all_keys(self) -> List[str]:
        """All keys combined"""
        return self.default_keys + self.sorted_keys
    
    @property
    def key_count(self) -> int:
        """Total number of keys"""
        return len(self.default_keys) + len(self.sorted_keys)


class YamlParser:
    """Parse patch.yaml and secrets.yaml files"""
    
    DEFAULT_KEYS = [
        'SERVICE_NAME', 'ENV', 'VERSION', 
        'HTTP_BASE_PATH', 'HTTP_SERVER_PORT', 'DB_NAME'
    ]
    SEPARATOR_PATTERN = re.compile(r'#-{20,}#')
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
    
    def parse_patch(self, path: str) -> Optional[ResourceData]:
        """Parse patch.yaml (HelmRelease)"""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            spec = data.get('spec', {})
            values = spec.get('values', {})
            deployment = values.get('deployment', {})
            resources = values.get('resources', {})
            autoscaling = values.get('autoscaling', {})
            
            # Extract service name from metadata
            service_name = data.get('metadata', {}).get('name', 'unknown')
            
            return ResourceData(
                service_name=service_name,
                replica_count=deployment.get('replicaCount'),
                cpu_limit=resources.get('limits', {}).get('cpu'),
                memory_limit=resources.get('limits', {}).get('memory'),
                cpu_request=resources.get('requests', {}).get('cpu'),
                memory_request=resources.get('requests', {}).get('memory'),
                autoscaling_enabled=autoscaling.get('enabled', False),
                min_replicas=autoscaling.get('minReplicas'),
                max_replicas=autoscaling.get('maxReplicas'),
            )
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error parsing {path}: {e}")
            return None
    
    def parse_secrets(self, path: str) -> Optional[EnvData]:
        """Parse secrets.yaml (Secret) - extract keys only, ignore values"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            # Try to parse YAML first
            try:
                data = yaml.safe_load(content)
                if data and 'stringData' in data:
                    string_data = data['stringData']
                    keys = list(string_data.keys())
                else:
                    # Fallback to regex extraction if YAML parsing fails
                    keys = self._extract_keys_regex(content)
            except yaml.YAMLError:
                # SOPS encrypted or malformed - use regex
                keys = self._extract_keys_regex(content)
            
            if not keys:
                return None
            
            # Extract service name from metadata
            service_name = data.get('metadata', {}).get('name', 'unknown') if 'data' in locals() else 'unknown'
            
            # Split into default keys and sorted keys
            default_keys, sorted_keys = self._split_keys(keys)
            
            return EnvData(
                service_name=service_name,
                default_keys=default_keys,
                sorted_keys=sorted_keys,
                raw_keys=keys
            )
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error parsing {path}: {e}")
            return None
    
    def _extract_keys_regex(self, content: str) -> List[str]:
        """Extract keys from SOPS-encrypted YAML using regex"""
        keys = []
        # Match key: value patterns (including encrypted values)
        pattern = re.compile(r'^(\w+(?:_\w+)*)\s*:', re.MULTILINE)
        matches = pattern.findall(content)
        
        # Filter out YAML document markers and special keys
        for key in matches:
            if key not in ['apiVersion', 'kind', 'metadata', 'spec', 'data', 'stringData', 'sops']:
                keys.append(key)
        
        return keys
    
    def _split_keys(self, keys: List[str]) -> Tuple[List[str], List[str]]:
        """Split keys into default keys and sorted keys based on separator"""
        default_keys = []
        sorted_keys = []
        
        # Find separator index
        separator_idx = -1
        for i, key in enumerate(keys):
            if self.SEPARATOR_PATTERN.search(key):
                separator_idx = i
                break
        
        if separator_idx == -1:
            # No separator found - try to identify default keys by presence
            for key in keys:
                if key in self.DEFAULT_KEYS:
                    default_keys.append(key)
                else:
                    sorted_keys.append(key)
        else:
            # Keys before separator are default keys (if they match DEFAULT_KEYS)
            # Keys after separator are sorted keys
            for key in keys:
                if key in self.DEFAULT_KEYS and len(default_keys) < 6:
                    default_keys.append(key)
                elif key not in self.DEFAULT_KEYS and key not in ['#-----------------Default ENV----------------------#', '#--------------------------------------------------#']:
                    sorted_keys.append(key)
        
        return default_keys, sorted_keys


def parse_memory_value(value: str) -> float:
    """Convert memory string to comparable float (in Mi)"""
    if not value:
        return 0.0
    
    value = str(value).strip()
    
    if value.endswith('Gi'):
        return float(value[:-2]) * 1024
    elif value.endswith('Mi'):
        return float(value[:-2])
    elif value.endswith('Ki'):
        return float(value[:-2]) / 1024
    elif value.endswith('G'):
        return float(value[:-1]) * 1024
    elif value.endswith('M'):
        return float(value[:-1])
    elif value.endswith('K'):
        return float(value[:-1]) / 1024
    else:
        # Plain number - assume Mi
        try:
            return float(value)
        except ValueError:
            return 0.0


def parse_cpu_value(value: str) -> float:
    """Convert CPU string to comparable float (in millicores)"""
    if not value:
        return 0.0
    
    value = str(value).strip()
    
    if value.endswith('m'):
        return float(value[:-1])
    else:
        # Plain number - assume cores
        try:
            return float(value) * 1000
        except ValueError:
            return 0.0

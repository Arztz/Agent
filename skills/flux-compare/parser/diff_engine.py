#!/usr/bin/env python3
"""
Diff Engine for Flux Compare skill.
Compares values and detects coverage/sorting issues.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from parser.yaml_parser import ResourceData, EnvData, YamlParser, parse_cpu_value, parse_memory_value
from parser.path_resolver import PathResolver, ServicePath


class ComparisonStatus(Enum):
    """Status for comparison results"""
    MATCHED = "matched"      # ✅ All environments are the same
    DIFFERENT = "different"  # ⚠️ Environments have different values
    INVALID = "invalid"      # ❌ Production has fewer keys than UAT/dev
    MISSING = "missing"      # ❌ Missing keys in some environment
    UNSORTED = "unsorted"    # ⚠️ Keys not alphabetically sorted
    NA = "na"               # N/A - Not available in this environment


@dataclass
class ResourceDiff:
    """Comparison result for resources"""
    service: str
    status: ComparisonStatus
    dev_rep: Optional[int] = None
    uat_rep: Optional[int] = None
    prod_rep: Optional[int] = None
    dev_cpu_req: Optional[str] = None
    uat_cpu_req: Optional[str] = None
    prod_cpu_req: Optional[str] = None
    dev_ram_req: Optional[str] = None
    uat_ram_req: Optional[str] = None
    prod_ram_req: Optional[str] = None
    dev_cpu_lim: Optional[str] = None
    uat_cpu_lim: Optional[str] = None
    prod_cpu_lim: Optional[str] = None
    dev_mem_lim: Optional[str] = None
    uat_mem_lim: Optional[str] = None
    prod_mem_lim: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    @property
    def status_icon(self) -> str:
        icons = {
            ComparisonStatus.MATCHED: "✅",
            ComparisonStatus.DIFFERENT: "⚠️",
            ComparisonStatus.INVALID: "❌",
            ComparisonStatus.MISSING: "❌",
            ComparisonStatus.NA: "N/A",
        }
        return icons.get(self.status, "?")


@dataclass
class EnvDiff:
    """Comparison result for ENV keys"""
    service: str
    status: ComparisonStatus
    dev_keys: int = 0
    uat_keys: int = 0
    prod_keys: int = 0
    # Actual keys in each environment
    dev_key_set: List[str] = field(default_factory=list)
    uat_key_set: List[str] = field(default_factory=list)
    prod_key_set: List[str] = field(default_factory=list)
    # Keys missing in each environment
    missing_in_dev: List[str] = field(default_factory=list)
    missing_in_uat: List[str] = field(default_factory=list)
    missing_in_prod: List[str] = field(default_factory=list)
    # Keys only in this environment (not in others)
    unique_to_dev: List[str] = field(default_factory=list)
    unique_to_uat: List[str] = field(default_factory=list)
    unique_to_prod: List[str] = field(default_factory=list)
    unsorted_in_dev: bool = False
    unsorted_in_uat: bool = False
    unsorted_in_prod: bool = False
    notes: List[str] = field(default_factory=list)
    
    @property
    def status_icon(self) -> str:
        icons = {
            ComparisonStatus.MATCHED: "✅",
            ComparisonStatus.DIFFERENT: "⚠️",
            ComparisonStatus.INVALID: "❌",
            ComparisonStatus.MISSING: "❌",
            ComparisonStatus.UNSORTED: "⚠️",
            ComparisonStatus.NA: "N/A",
        }
        return icons.get(self.status, "?")
    
    @property
    def status_text(self) -> str:
        if self.status == ComparisonStatus.MATCHED:
            return "same structure"
        elif self.status == ComparisonStatus.DIFFERENT:
            parts = []
            if self.missing_in_dev:
                parts.append(f"dev -")
            if self.missing_in_uat:
                parts.append(f"uat -" if self.missing_in_uat else "")
            return ", ".join(parts) if parts else "diff"
        elif self.status == ComparisonStatus.INVALID:
            if self.missing_in_prod:
                return "prod -"
            return "invalid"
        elif self.status == ComparisonStatus.UNSORTED:
            unsorted = []
            if self.unsorted_in_dev:
                unsorted.append("dev")
            if self.unsorted_in_uat:
                unsorted.append("uat")
            if self.unsorted_in_prod:
                unsorted.append("prod")
            return f"unsorted: {', '.join(unsorted)}"
        return ""
        return ""


class DiffEngine:
    """Compare resources and ENV keys across environments"""
    
    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.parser = YamlParser(repo_root)
        self.resolver = PathResolver(repo_root)
    
    def compare_resources(self, sp: ServicePath) -> ResourceDiff:
        """Compare resources for a service across environments"""
        # Parse all environment patches
        dev_data = self.parser.parse_patch(sp.dev_patch) if sp.dev_patch else None
        uat_data = self.parser.parse_patch(sp.uat_patch) if sp.uat_patch else None
        prod_data = self.parser.parse_patch(sp.prod_patch) if sp.prod_patch else None
        
        # Determine status
        if not all([sp.dev_patch, sp.uat_patch, sp.prod_patch]):
            status = ComparisonStatus.MISSING
        elif not dev_data and not uat_data and not prod_data:
            status = ComparisonStatus.NA
        else:
            # Compare values
            dev_rep = dev_data.replica_count if dev_data else None
            uat_rep = uat_data.replica_count if uat_data else None
            prod_rep = prod_data.replica_count if prod_data else None
            
            # Check if all are the same
            if dev_rep == uat_rep == prod_rep and dev_rep is not None:
                status = ComparisonStatus.MATCHED
            elif prod_rep is not None and uat_rep is not None and prod_rep < uat_rep:
                status = ComparisonStatus.INVALID
            else:
                status = ComparisonStatus.DIFFERENT
        
        return ResourceDiff(
            service=sp.name,
            status=status,
            dev_rep=dev_data.replica_count if dev_data else None,
            uat_rep=uat_data.replica_count if uat_data else None,
            prod_rep=prod_data.replica_count if prod_data else None,
            # requests.cpu
            dev_cpu_req=dev_data.cpu_request if dev_data else None,
            uat_cpu_req=uat_data.cpu_request if uat_data else None,
            prod_cpu_req=prod_data.cpu_request if prod_data else None,
            # requests.ram
            dev_ram_req=dev_data.memory_request if dev_data else None,
            uat_ram_req=uat_data.memory_request if uat_data else None,
            prod_ram_req=prod_data.memory_request if prod_data else None,
            # limits.cpu
            dev_cpu_lim=dev_data.cpu_limit if dev_data else None,
            uat_cpu_lim=uat_data.cpu_limit if uat_data else None,
            prod_cpu_lim=prod_data.cpu_limit if prod_data else None,
            # limits.ram
            dev_mem_lim=dev_data.memory_limit if dev_data else None,
            uat_mem_lim=uat_data.memory_limit if uat_data else None,
            prod_mem_lim=prod_data.memory_limit if prod_data else None,
            notes=[]
        )
    
    def compare_env(self, sp: ServicePath) -> EnvDiff:
        """Compare ENV keys for a service across environments"""
        # Parse all environment secrets
        dev_data = self.parser.parse_secrets(sp.dev_secrets) if sp.dev_secrets else None
        uat_data = self.parser.parse_secrets(sp.uat_secrets) if sp.uat_secrets else None
        prod_data = self.parser.parse_secrets(sp.prod_secrets) if sp.prod_secrets else None
        
        # Get key sets
        dev_keys_set = set(dev_data.all_keys) if dev_data else set()
        uat_keys_set = set(uat_data.all_keys) if uat_data else set()
        prod_keys_set = set(prod_data.all_keys) if prod_data else set()
        
        dev_count = len(dev_keys_set)
        uat_count = len(uat_keys_set)
        prod_count = len(prod_keys_set)
        
        # Keys in each environment
        dev_key_list = sorted(list(dev_data.all_keys)) if dev_data else []
        uat_key_list = sorted(list(uat_data.all_keys)) if uat_data else []
        prod_key_list = sorted(list(prod_data.all_keys)) if prod_data else []
        
        # Find missing keys (prod should have all, uat should have all that prod has, etc.)
        # missing_in_dev = keys that exist in UAT or PROD but not in DEV
        missing_in_dev = sorted(list((uat_keys_set | prod_keys_set) - dev_keys_set))
        # missing_in_uat = keys that exist in PROD but not in UAT
        missing_in_uat = sorted(list(prod_keys_set - uat_keys_set))
        # missing_in_prod = keys that exist in UAT or DEV but not in PROD (invalid state)
        missing_in_prod = sorted(list((dev_keys_set | uat_keys_set) - prod_keys_set))
        
        # Unique keys (exist only in one environment)
        unique_to_dev = sorted(list(dev_keys_set - uat_keys_set - prod_keys_set))
        unique_to_uat = sorted(list(uat_keys_set - dev_keys_set - prod_keys_set))
        unique_to_prod = sorted(list(prod_keys_set - dev_keys_set - uat_keys_set))
        
        # Check sorting
        unsorted_dev = self._check_unsorted(dev_data.sorted_keys) if dev_data else False
        unsorted_uat = self._check_unsorted(uat_data.sorted_keys) if uat_data else False
        unsorted_prod = self._check_unsorted(prod_data.sorted_keys) if prod_data else False
        
        # Determine status
        if not all([sp.dev_secrets, sp.uat_secrets, sp.prod_secrets]):
            status = ComparisonStatus.MISSING
        elif not dev_data and not uat_data and not prod_data:
            status = ComparisonStatus.NA
        elif prod_count < uat_count or prod_count < dev_count or missing_in_prod:
            status = ComparisonStatus.INVALID
        elif dev_count != uat_count or uat_count != prod_count:
            status = ComparisonStatus.DIFFERENT
        elif unsorted_dev or unsorted_uat or unsorted_prod:
            status = ComparisonStatus.UNSORTED
        elif missing_in_dev or missing_in_uat or unique_to_dev or unique_to_uat or unique_to_prod:
            status = ComparisonStatus.DIFFERENT
        else:
            status = ComparisonStatus.MATCHED
        
        return EnvDiff(
            service=sp.name,
            status=status,
            dev_keys=dev_count,
            uat_keys=uat_count,
            prod_keys=prod_count,
            dev_key_set=dev_key_list,
            uat_key_set=uat_key_list,
            prod_key_set=prod_key_list,
            missing_in_dev=missing_in_dev,
            missing_in_uat=missing_in_uat,
            missing_in_prod=missing_in_prod,
            unique_to_dev=unique_to_dev,
            unique_to_uat=unique_to_uat,
            unique_to_prod=unique_to_prod,
            unsorted_in_dev=unsorted_dev,
            unsorted_in_uat=unsorted_uat,
            unsorted_in_prod=unsorted_prod
        )
    
    def _check_unsorted(self, keys: List[str]) -> bool:
        """Check if keys are not alphabetically sorted"""
        if not keys:
            return False
        return keys != sorted(keys)
    
    def compare_all_resources(self, type: str) -> List[ResourceDiff]:
        """Compare resources for all services of a type"""
        all_paths = self.resolver.resolve_all_services(type)
        return [self.compare_resources(sp) for sp in all_paths]
    
    def compare_all_env(self, type: str) -> List[EnvDiff]:
        """Compare ENV keys for all services of a type"""
        all_paths = self.resolver.resolve_all_services(type)
        return [self.compare_env(sp) for sp in all_paths]
    
    def get_fix_suggestion(self, env_data: EnvData, expected_keys: set) -> Dict[str, Any]:
        """Generate fix suggestions for a service's secrets.yaml"""
        current_keys = set(env_data.raw_keys)
        expected_all_keys = expected_keys
        
        missing = expected_all_keys - current_keys
        extra = current_keys - expected_all_keys
        
        # Suggest sorting
        default_section = env_data.default_keys
        sorted_section = sorted(env_data.sorted_keys)
        
        return {
            'missing': sorted(missing),
            'extra': sorted(extra),
            'suggested_default_order': default_section,
            'suggested_sorted_order': sorted_section
        }

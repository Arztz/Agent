#!/usr/bin/env python3
"""
Main logic for Flux Compare skill.
Scans and compares environment overlays with interactive fix capability.
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add skill directory to path
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from parser import DiffEngine, ComparisonStatus, EnvDiff
from parser.path_resolver import PathResolver
from parser.yaml_parser import YamlParser
from formatters import TableFormatter, TableConfig


class FluxCompare:
    """Main class for Flux Compare skill"""
    
    VALID_TYPES = ['apps', 'clusters', 'dependencies', 'infrastructure', 'operator']
    VALID_MODES = ['resource', 'env', 'both']
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.diff_engine = DiffEngine(str(repo_root))
        self.resolver = PathResolver(str(repo_root))
        self.parser = YamlParser(str(repo_root))
        self.formatter = TableFormatter(TableConfig(color_enabled=True))
    
    def scan(self, type: str, mode: str = 'both') -> Tuple[List, List]:
        """Scan and compare all services of a type"""
        if type not in self.VALID_TYPES:
            raise ValueError(f"Invalid type: {type}. Valid types: {self.VALID_TYPES}")
        
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}. Valid modes: {self.VALID_MODES}")
        
        resource_results = []
        env_results = []
        
        if mode in ['resource', 'both']:
            resource_results = self.diff_engine.compare_all_resources(type)
        
        if mode in ['env', 'both']:
            env_results = self.diff_engine.compare_all_env(type)
        
        return resource_results, env_results
    
    def report(self, type: str, mode: str = 'both') -> str:
        """Generate comparison report"""
        resource_results, env_results = self.scan(type, mode)
        
        repo_root = str(self.repo_root)
        
        lines = []
        lines.append(f"\n\033[34mFlux Compare: {type} ({mode})\033[0m")
        lines.append(f"\033[36mRepository: {self.repo_root}\033[0m")
        
        if mode in ['resource', 'both']:
            lines.append(self.formatter.format_resource_table_v2(resource_results))
        
        if mode in ['env', 'both']:
            lines.append(self.formatter.format_env_output_for_fix(env_results))
        
        if mode == 'both':
            lines.append(self.formatter.format_summary(resource_results, env_results))
        
        return "\n".join(lines)
    
    def get_services_needing_fix(self, env_results: List[EnvDiff]) -> List[EnvDiff]:
        """Get list of services that need ENV key fixes"""
        return [
            r for r in env_results 
            if r.status != ComparisonStatus.MATCHED
        ]
    
    def interactive_fix(self, type: str, env_results: List[EnvDiff]) -> None:
        """Interactive fix: ask user service by service"""
        needs_fix = self.get_services_needing_fix(env_results)
        
        if not needs_fix:
            print(self.formatter._colorize("\n✅ All services have correct ENV structure!", 
                                           self.formatter.colors.GREEN))
            return
        
        print(self.formatter._colorize(f"\n=== INTERACTIVE FIX ({len(needs_fix)} services need fixes) ===", 
                                       self.formatter.colors.BOLD + self.formatter.colors.CYAN))
        print("\nOptions: y=yes, n=no (skip), q=quit fix mode")
        print()
        
        fixed = []
        skipped = []
        
        for result in needs_fix:
            print(self.formatter.format_detailed_env_issues(result))
            
            # Show detailed missing keys if any
            if result.missing_in_dev:
                print(f"  Keys to add to dev: {', '.join(result.missing_in_dev)}")
            if result.missing_in_uat:
                print(f"  Keys to add to uat: {', '.join(result.missing_in_uat)}")
            
            if result.unsorted_in_dev or result.unsorted_in_uat or result.unsorted_in_prod:
                print("  Action: Re-sort keys alphabetically after separator")
            
            while True:
                response = input(f"\nFix {result.service}? [y/N/q]: ").strip().lower()
                if response == 'q':
                    print("\nFix session ended.")
                    print(f"Fixed: {len(fixed)} services")
                    print(f"Skipped: {len(skipped)} services")
                    return
                elif response == 'y':
                    self._fix_service_env(type, result)
                    fixed.append(result.service)
                    break
                elif response in ['', 'n']:
                    skipped.append(result.service)
                    break
                else:
                    print("Please enter y, n, or q")
        
        print("\n" + self.formatter._colorize("Fix session complete!", self.formatter.colors.GREEN))
        print(f"Fixed: {len(fixed)} services")
        print(f"Skipped: {len(skipped)} services")
    
    def _fix_service_env(self, type: str, result: EnvDiff) -> bool:
        """Fix a single service's secrets.yaml files"""
        service = result.service
        resolver = PathResolver(str(self.repo_root))
        sp = resolver.resolve_service_paths(type, service)
        
        fixed_files = []
        
        # Fix each environment that needs it
        for env_name, secrets_path in [('develop', sp.dev_secrets), ('uat', sp.uat_secrets), ('prod', sp.prod_secrets)]:
            if not secrets_path:
                continue
            
            issues = []
            if env_name == 'develop' and result.missing_in_dev:
                issues.append('missing_keys')
            if env_name == 'uat' and result.missing_in_uat:
                issues.append('missing_keys')
            if env_name == 'develop' and result.unsorted_in_dev:
                issues.append('unsorted')
            if env_name == 'uat' and result.unsorted_in_uat:
                issues.append('unsorted')
            if env_name == 'prod' and result.unsorted_in_prod:
                issues.append('unsorted')
            
            if not issues:
                continue
            
            try:
                self._fix_single_file(secrets_path, env_name, result)
                fixed_files.append(f"{env_name}/{service}")
            except Exception as e:
                print(self.formatter._colorize(f"  Error fixing {env_name}: {e}", 
                                               self.formatter.colors.RED))
        
        if fixed_files:
            print(self.formatter._colorize(f"  ✅ Fixed: {', '.join(fixed_files)}", 
                                           self.formatter.colors.GREEN))
            return True
        return False
    
    def _fix_single_file(self, path: str, env_name: str, result: EnvDiff) -> None:
        """Fix a single secrets.yaml file"""
        # Read current content
        with open(path, 'r') as f:
            content = f.read()
        
        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            print(self.formatter._colorize(f"  ⚠️ Cannot parse {path} - may be SOPS encrypted", 
                                           self.formatter.colors.YELLOW))
            return
        
        if not data or 'stringData' not in data:
            return
        
        string_data = data['stringData']
        
        # Get all keys
        all_keys = list(string_data.keys())
        
        # Identify default keys (first 6 that match DEFAULT_KEYS)
        default_keys = []
        sorted_keys = []
        
        for key in all_keys:
            if key in YamlParser.DEFAULT_KEYS and len(default_keys) < 6:
                default_keys.append(key)
            elif key not in ['#-----------------Default ENV----------------------#', '#--------------------------------------------------#']:
                sorted_keys.append(key)
        
        # Sort the sorted section
        sorted_keys.sort()
        
        # Reconstruct stringData in correct order
        new_string_data = {}
        
        # Add separator comment
        new_string_data['#-----------------Default ENV----------------------#'] = None
        
        # Add default keys with their values
        for key in default_keys:
            if key in string_data:
                new_string_data[key] = string_data[key]
        
        # Add separator end
        new_string_data['#--------------------------------------------------#'] = None
        
        # Add sorted keys
        for key in sorted_keys:
            if key in string_data:
                new_string_data[key] = string_data[key]
        
        # Update data
        data['stringData'] = new_string_data
        
        # Write back
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def generate_fix_script(self, type: str, env_results: List[EnvDiff]) -> str:
        """Generate a bash script to fix all services"""
        needs_fix = self.get_services_needing_fix(env_results)
        
        if not needs_fix:
            return "# No fixes needed"
        
        lines = ["#!/bin/bash", "# Generated fix script for flux-compare", "", 
                 f"# Type: {type}", f"# Services needing fix: {len(needs_fix)}", ""]
        
        for result in needs_fix:
            lines.append(f"# === {result.service} ===")
            if result.missing_in_dev:
                lines.append(f"# Missing in dev: {', '.join(result.missing_in_dev)}")
            if result.missing_in_uat:
                lines.append(f"# Missing in uat: {', '.join(result.missing_in_uat)}")
            if result.unsorted_in_dev:
                lines.append("# Action: Sort keys alphabetically after separator in dev")
            if result.unsorted_in_uat:
                lines.append("# Action: Sort keys alphabetically after separator in uat")
            if result.unsorted_in_prod:
                lines.append("# Action: Sort keys alphabetically after separator in prod")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flux Compare - Compare environment overlays')
    parser.add_argument('type', choices=FluxCompare.VALID_TYPES, help='Component type')
    parser.add_argument('mode', nargs='?', choices=FluxCompare.VALID_MODES, default='both', 
                        help='Comparison mode (default: both)')
    parser.add_argument('--repo', default='.', help='Repository root (default: current dir)')
    parser.add_argument('--fix', action='store_true', help='Run interactive fix mode')
    parser.add_argument('--script', action='store_true', help='Generate fix script instead of running')
    
    args = parser.parse_args()
    
    fc = FluxCompare(args.repo)
    
    if args.fix:
        _, env_results = fc.scan(args.type, 'env')
        fc.interactive_fix(args.type, env_results)
    elif args.script:
        _, env_results = fc.scan(args.type, 'env')
        print(fc.generate_fix_script(args.type, env_results))
    else:
        print(fc.report(args.type, args.mode))


if __name__ == '__main__':
    main()

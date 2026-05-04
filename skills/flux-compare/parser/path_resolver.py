#!/usr/bin/env python3
"""
Path Resolver for Flux Compare skill.
Maps type (apps/clusters/infra/operator/deps) to file paths.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ServicePath:
    """Paths for a single service across environments"""
    name: str
    type: str
    
    # Environment paths for patch.yaml
    dev_patch: Optional[str] = None
    uat_patch: Optional[str] = None
    prod_patch: Optional[str] = None
    
    # Environment paths for secrets.yaml
    dev_secrets: Optional[str] = None
    uat_secrets: Optional[str] = None
    prod_secrets: Optional[str] = None
    
    @property
    def patch_paths(self) -> Dict[str, Optional[str]]:
        return {'develop': self.dev_patch, 'uat': self.uat_patch, 'prod': self.prod_patch}
    
    @property
    def secrets_paths(self) -> Dict[str, Optional[str]]:
        return {'develop': self.dev_secrets, 'uat': self.uat_secrets, 'prod': self.prod_secrets}


class PathResolver:
    """Resolve service paths by type"""
    
    # Environment mappings by type
    ENV_MAPPINGS = {
        'apps': {
            'develop': 'apps/develop',
            'uat': 'apps/uat', 
            'prod': 'apps/prod'
        },
        'clusters': {
            'develop': 'clusters/develop',
            'uat': 'clusters/uat',
            'prod': 'clusters/prod'
        },
        'infrastructure': {
            'develop': 'infrastructure/nonprod',  # Note: nonprod for dev equivalent
            'uat': 'infrastructure/uat',
            'prod': 'infrastructure/prod'
        },
        'operator': {
            'develop': 'operator/nonprod',
            'uat': 'operator/uat',
            'prod': 'operator/prod'
        },
        'dependencies': {
            'develop': 'dependencies/develop',
            'uat': 'dependencies/uat',
            'prod': 'dependencies/prod'
        }
    }
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.type_envs = {
            'apps': ['develop', 'uat', 'prod'],
            'clusters': ['develop', 'uat', 'prod'],
            'infrastructure': ['develop', 'uat', 'prod'],
            'operator': ['develop', 'uat', 'prod'],
            'dependencies': ['develop', 'uat', 'prod'],
        }
    
    def get_services_by_type(self, type: str) -> List[str]:
        """Get all service names for a given type"""
        if type not in self.ENV_MAPPINGS:
            raise ValueError(f"Unknown type: {type}")
        
        services = set()
        
        # Get services from base directory
        base_dir = self.repo_root / type / 'base'
        if base_dir.exists():
            for item in base_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    services.add(item.name)
        
        # Also check each environment directory
        for env_key, env_path in self.ENV_MAPPINGS[type].items():
            env_dir = self.repo_root / env_path
            if env_dir.exists():
                for item in env_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        services.add(item.name)
        
        return sorted(services)
    
    def resolve_service_paths(self, type: str, service: str) -> ServicePath:
        """Resolve all paths for a single service"""
        if type not in self.ENV_MAPPINGS:
            raise ValueError(f"Unknown type: {type}")
        
        sp = ServicePath(name=service, type=type)
        
        for env_key, env_path in self.ENV_MAPPINGS[type].items():
            service_dir = self.repo_root / env_path / service
            
            # Check for patch.yaml
            patch_path = service_dir / 'patch.yaml'
            if patch_path.exists():
                if env_key == 'develop':
                    sp.dev_patch = str(patch_path)
                elif env_key == 'uat':
                    sp.uat_patch = str(patch_path)
                elif env_key == 'prod':
                    sp.prod_patch = str(patch_path)
            
            # Check for secrets.yaml
            secrets_path = service_dir / 'secrets.yaml'
            if secrets_path.exists():
                if env_key == 'develop':
                    sp.dev_secrets = str(secrets_path)
                elif env_key == 'uat':
                    sp.uat_secrets = str(secrets_path)
                elif env_key == 'prod':
                    sp.prod_secrets = str(secrets_path)
        
        return sp
    
    def resolve_all_services(self, type: str) -> List[ServicePath]:
        """Resolve paths for all services of a type"""
        services = self.get_services_by_type(type)
        return [self.resolve_service_paths(type, s) for s in services]
    
    def get_type_envs(self, type: str) -> List[str]:
        """Get environment list for a type"""
        return self.type_envs.get(type, ['develop', 'uat', 'prod'])
    
    def get_env_key_mapping(self, type: str) -> Dict[str, str]:
        """Get internal to display environment key mapping"""
        return self.ENV_MAPPINGS.get(type, {})

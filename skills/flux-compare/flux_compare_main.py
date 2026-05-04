#!/usr/bin/env python3
"""
Flux Compare - Main invocation script for skill.
Entry point when /flux-compare is triggered.
"""

import sys
import os
from pathlib import Path

# Add skill directory to path
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from flux_compare import FluxCompare


def invoke(args: str) -> str:
    """
    Main invocation function for the skill.
    
    Args:
        args: Command arguments in format "type [mode]"
              type: apps|clusters|dependencies|infrastructure|operator
              mode: resource|env|both (default: both)
    
    Returns:
        Comparison report as formatted string
    """
    # Parse arguments
    parts = args.strip().split()
    type_arg = parts[0] if len(parts) > 0 else 'apps'
    mode_arg = parts[1] if len(parts) > 1 else 'both'
    
    # Validate
    valid_types = ['apps', 'clusters', 'dependencies', 'infrastructure', 'operator']
    valid_modes = ['resource', 'env', 'both']
    
    if type_arg not in valid_types:
        return f"❌ Invalid type: {type_arg}\nValid types: {', '.join(valid_types)}"
    
    if mode_arg not in valid_modes:
        return f"❌ Invalid mode: {mode_arg}\nValid modes: {', '.join(valid_modes)}"
    
    # Get repo root (parent of .opencode)
    repo_root = SKILL_DIR.parent.parent.parent
    repo_root_str = str(repo_root)
    
    # Run comparison
    fc = FluxCompare(repo_root_str)
    
    try:
        return fc.report(type_arg, mode_arg)
    except Exception as e:
        return f"❌ Error: {str(e)}"


def invoke_fix(args: str) -> str:
    """
    Invoke interactive fix mode.
    
    Args:
        args: Command arguments in format "type"
              type: apps|clusters|dependencies|infrastructure|operator
    
    Returns:
        Interactive fix results
    """
    parts = args.strip().split()
    type_arg = parts[0] if len(parts) > 0 else 'apps'
    
    repo_root = SKILL_DIR.parent.parent.parent
    fc = FluxCompare(str(repo_root))
    
    try:
        _, env_results = fc.scan(type_arg, 'env')
        # This will run interactively - output goes to stdout
        fc.interactive_fix(type_arg, env_results)
        return "Fix session completed."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def invoke_script(args: str) -> str:
    """
    Generate fix script.
    
    Args:
        args: Command arguments in format "type"
              type: apps|clusters|dependencies|infrastructure|operator
    
    Returns:
        Generated bash script
    """
    parts = args.strip().split()
    type_arg = parts[0] if len(parts) > 0 else 'apps'
    
    repo_root = SKILL_DIR.parent.parent.parent
    fc = FluxCompare(str(repo_root))
    
    try:
        _, env_results = fc.scan(type_arg, 'env')
        return fc.generate_fix_script(type_arg, env_results)
    except Exception as e:
        return f"❌ Error: {str(e)}"


# If run directly
if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(invoke(' '.join(sys.argv[1:])))
    else:
        print("Usage: python flux_compare_main.py <type> [mode]")
        print("  type: apps|clusters|dependencies|infrastructure|operator")
        print("  mode: resource|env|both (default: both)")

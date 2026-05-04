#!/usr/bin/env python3
"""
Table Formatter for Flux Compare skill.
Generates colorized ASCII tables for terminal output.
"""

from typing import List, Optional
from dataclasses import dataclass
from parser.diff_engine import ComparisonStatus, ResourceDiff, EnvDiff


# ANSI Color Codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Status colors
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    
    # Dim colors
    DIM = "\033[2m"
    DIM_RED = "\033[91m"
    DIM_GREEN = "\033[92m"
    DIM_YELLOW = "\033[93m"


@dataclass
class TableConfig:
    """Configuration for table formatting"""
    show_dev: bool = True
    show_uat: bool = True
    show_prod: bool = True
    color_enabled: bool = True


class TableFormatter:
    """Generate ASCII tables with ANSI colors"""
    
    # Box drawing characters
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    TOP_MID = "┬"
    MID_MID = "┼"
    BOTTOM_MID = "┴"
    VERTICAL = "│"
    HORIZONTAL = "─"
    
    def __init__(self, config: Optional[TableConfig] = None):
        self.config = config or TableConfig()
        self.colors = Colors()
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color if enabled"""
        if not self.config.color_enabled:
            return text
        return f"{color}{text}{self.colors.RESET}"
    
    def _header(self, text: str, width: int) -> str:
        """Format header cell"""
        padded = text.center(width)
        return self._colorize(padded, self.colors.BLUE + self.colors.BOLD)
    
    def _cell(self, text: str, width: int, color: str = "") -> str:
        """Format regular cell"""
        if text is None or text == "N/A":
            text = "N/A"
        padded = str(text).center(width)
        return self._colorize(padded, color)
    
    def _cell_left(self, text: str, width: int, color: str = "") -> str:
        """Format cell with left alignment"""
        if text is None:
            text = ""
        padded = str(text)[:width].ljust(width)
        return self._colorize(padded, color)
    
    def _status_color(self, status: ComparisonStatus) -> str:
        """Get color for status"""
        colors_map = {
            ComparisonStatus.MATCHED: self.colors.GREEN,
            ComparisonStatus.DIFFERENT: self.colors.YELLOW,
            ComparisonStatus.INVALID: self.colors.RED,
            ComparisonStatus.MISSING: self.colors.RED,
            ComparisonStatus.UNSORTED: self.colors.YELLOW,
            ComparisonStatus.NA: self.colors.DIM,
        }
        return colors_map.get(status, "")
    
    def _hline(self, widths: List[int]) -> str:
        """Generate horizontal line"""
        line = self.TOP_LEFT
        for i, w in enumerate(widths):
            line += self.HORIZONTAL * (w + 2)
            if i < len(widths) - 1:
                line += self.TOP_MID
            else:
                line += self.TOP_RIGHT
        return line
    
    def _hline_mid(self, widths: List[int]) -> str:
        """Generate middle horizontal line"""
        line = self.VERTICAL
        for i, w in enumerate(widths):
            line += self.HORIZONTAL * (w + 2) + self.VERTICAL
        return line
    
    def _hline_bottom(self, widths: List[int]) -> str:
        """Generate bottom horizontal line"""
        line = self.BOTTOM_LEFT
        for i, w in enumerate(widths):
            line += self.HORIZONTAL * (w + 2)
            if i < len(widths) - 1:
                line += self.BOTTOM_MID
            else:
                line += self.BOTTOM_RIGHT
        return line
    
    def format_resource_table_v2(self, results: List[ResourceDiff]) -> str:
        """
        Format resource comparison for VISUAL COMPARISON.
        Each service shows 5 resource lines with DEV | UAT | PROD values.
        """
        if not results:
            return self._colorize("No resource data found.", self.colors.YELLOW)
        
        # Sort: errors first, then different, then matched
        def sort_key(r: ResourceDiff) -> tuple:
            status_order = {
                ComparisonStatus.INVALID: 0,
                ComparisonStatus.MISSING: 0,
                ComparisonStatus.DIFFERENT: 1,
                ComparisonStatus.UNSORTED: 1,
                ComparisonStatus.MATCHED: 2,
                ComparisonStatus.NA: 3,
            }
            return (status_order.get(r.status, 99), r.service)
        
        sorted_results = sorted(results, key=sort_key)
        
        # Column widths
        service_width = 20
        resource_width = 72  # For "replicas: X | Y | Z" format
        
        lines = []
        lines.append(self._colorize("\n=== RESOURCE COMPARISON ===", self.colors.BOLD + self.colors.CYAN))
        lines.append("")
        lines.append(self._colorize("For visual comparison - check for highlighted differences", self.colors.DIM))
        lines.append("")
        
        # Table header
        lines.append(self.TOP_LEFT + self.HORIZONTAL * (service_width + 2) + 
                   self.TOP_MID + self.HORIZONTAL * (resource_width + 2) + self.TOP_RIGHT)
        header = self.VERTICAL + " Service ".ljust(service_width + 1) + self.VERTICAL
        header += " Resource Comparison (DEV | UAT | PROD) ".ljust(resource_width + 1) + self.VERTICAL
        lines.append(self._colorize(header, self.colors.BLUE + self.colors.BOLD))
        lines.append(self._hline_mid([service_width, resource_width]))
        
        # Data rows
        for r in sorted_results:
            # Service column (spans 5 rows conceptually, but we show once)
            service_col = r.service
            
            # Prepare 5 resource lines
            resource_lines = []
            
            # 1. replicas
            dev_rep = str(r.dev_rep) if r.dev_rep is not None else "N/A"
            uat_rep = str(r.uat_rep) if r.uat_rep is not None else "N/A"
            prod_rep = str(r.prod_rep) if r.prod_rep is not None else "N/A"
            rep_diff = not (r.dev_rep == r.uat_rep == r.prod_rep and r.dev_rep is not None)
            resource_lines.append(("replicas:", dev_rep, uat_rep, prod_rep, rep_diff))
            
            # 2. requests.cpu
            dev_cpu_req = r.dev_cpu_req if hasattr(r, 'dev_cpu_req') and r.dev_cpu_req else "-"
            uat_cpu_req = r.uat_cpu_req if hasattr(r, 'uat_cpu_req') and r.uat_cpu_req else "-"
            prod_cpu_req = r.prod_cpu_req if hasattr(r, 'prod_cpu_req') and r.prod_cpu_req else "-"
            cpu_req_diff = dev_cpu_req != uat_cpu_req or uat_cpu_req != prod_cpu_req
            resource_lines.append(("requests.cpu:", str(dev_cpu_req), str(uat_cpu_req), str(prod_cpu_req), cpu_req_diff))
            
            # 3. requests.ram
            dev_ram_req = r.dev_ram_req if hasattr(r, 'dev_ram_req') and r.dev_ram_req else "-"
            uat_ram_req = r.uat_ram_req if hasattr(r, 'uat_ram_req') and r.uat_ram_req else "-"
            prod_ram_req = r.prod_ram_req if hasattr(r, 'prod_ram_req') and r.prod_ram_req else "-"
            ram_req_diff = str(dev_ram_req) != str(uat_ram_req) or str(uat_ram_req) != str(prod_ram_req)
            resource_lines.append(("requests.ram:", str(dev_ram_req), str(uat_ram_req), str(prod_ram_req), ram_req_diff))
            
            # 4. limits.cpu
            dev_cpu_lim = r.dev_cpu_lim if r.dev_cpu_lim else "-"
            uat_cpu_lim = r.uat_cpu_lim if r.uat_cpu_lim else "-"
            prod_cpu_lim = r.prod_cpu_lim if r.prod_cpu_lim else "-"
            cpu_lim_diff = dev_cpu_lim != uat_cpu_lim or uat_cpu_lim != prod_cpu_lim
            resource_lines.append(("limits.cpu:", str(dev_cpu_lim), str(uat_cpu_lim), str(prod_cpu_lim), cpu_lim_diff))
            
            # 5. limits.ram
            dev_ram_lim = r.dev_mem_lim if r.dev_mem_lim else "-"
            uat_ram_lim = r.uat_mem_lim if r.uat_mem_lim else "-"
            prod_ram_lim = r.prod_mem_lim if r.prod_mem_lim else "-"
            ram_lim_diff = str(dev_ram_lim) != str(uat_ram_lim) or str(uat_ram_lim) != str(prod_ram_lim)
            resource_lines.append(("limits.ram:", str(dev_ram_lim), str(uat_ram_lim), str(prod_ram_lim), ram_lim_diff))
            
            # Render each line
            for i, (label, dev, uat, prod, is_diff) in enumerate(resource_lines):
                if i == 0:
                    # First line - include service name
                    row = self.VERTICAL + service_col.ljust(service_width + 1) + self.VERTICAL
                else:
                    row = self.VERTICAL + "".ljust(service_width + 1) + self.VERTICAL
                
                # Build resource value string
                val_str = f"{label} {dev} | {uat} | {prod}"
                
                # Color based on whether different
                if is_diff:
                    val_color = self.colors.YELLOW
                    # Highlight the differing values
                    val_parts = []
                    if dev != uat:
                        val_parts.append(dev)
                    else:
                        val_parts.append(dev)
                    if uat != prod:
                        val_parts.append(uat)
                    else:
                        val_parts.append(uat)
                    if prod != dev:
                        val_parts.append(prod)
                    else:
                        val_parts.append(prod)
                    val_str = f"{label} {val_parts[0]} | {val_parts[1]} | {val_parts[2]}"
                else:
                    val_color = ""
                
                row += val_str.ljust(resource_width + 1) + self.VERTICAL
                lines.append(self._colorize(row, val_color))
            
            # Add separator between services
            lines.append(self._hline_mid([service_width, resource_width]))
        
        lines.append(self.BOTTOM_LEFT + self.HORIZONTAL * (service_width + 2) + 
                    self.BOTTOM_MID + self.HORIZONTAL * (resource_width + 2) + self.BOTTOM_RIGHT)
        
        # Legend
        lines.append("")
        lines.append(self._colorize("Legend: ", self.colors.BOLD) + 
                   f"{self._colorize('No highlight = all match', self.colors.DIM)}  " +
                   f"{self._colorize('Yellow = values differ', self.colors.YELLOW)}")
        
        return "\n".join(lines)
    
    def format_env_table_detailed(self, results: List[EnvDiff]) -> str:
        """
        Format ENV comparison results as detailed table showing each key.
        Table shows: Service | DEV | UAT | PROD | Status
        Each cell shows keys present in that environment.
        """
        if not results:
            return self._colorize("No ENV data found.", self.colors.YELLOW)
        
        # Sort: errors first, then different, then matched
        def sort_key(r: EnvDiff) -> tuple:
            status_order = {
                ComparisonStatus.INVALID: 0,
                ComparisonStatus.MISSING: 0,
                ComparisonStatus.DIFFERENT: 1,
                ComparisonStatus.UNSORTED: 1,
                ComparisonStatus.MATCHED: 2,
                ComparisonStatus.NA: 3,
            }
            return (status_order.get(r.status, 99), r.service)
        
        sorted_results = sorted(results, key=sort_key)
        
        # Column widths
        widths = [22, 40, 40, 40, 12]  # service, dev, uat, prod, status
        
        # Header
        headers = ["Service", "DEV keys", "UAT keys", "PROD keys", "Status"]
        
        # Build table
        lines = []
        lines.append(self._colorize("\n=== ENV KEY COMPARISON ===", self.colors.BOLD + self.colors.CYAN))
        lines.append("")
        lines.append(self._hline(widths))
        
        # Header row
        header_row = self.VERTICAL
        for h, w in zip(headers, widths):
            header_row += self._header(h, w) + self.VERTICAL
        lines.append(header_row)
        lines.append(self._hline_mid(widths))
        
        # Data rows
        for r in sorted_results:
            row = self.VERTICAL
            
            # Service name
            row += self._cell_left(r.service, widths[0]) + self.VERTICAL
            
            # DEV keys (truncated if too long)
            dev_keys_str = ', '.join(r.dev_key_set) if r.dev_key_set else "(none)"
            if len(dev_keys_str) > widths[1]:
                dev_keys_str = dev_keys_str[:widths[1]-3] + "..."
            row += self._cell_left(dev_keys_str, widths[1]) + self.VERTICAL
            
            # UAT keys
            uat_keys_str = ', '.join(r.uat_key_set) if r.uat_key_set else "(none)"
            if len(uat_keys_str) > widths[2]:
                uat_keys_str = uat_keys_str[:widths[2]-3] + "..."
            row += self._cell_left(uat_keys_str, widths[2]) + self.VERTICAL
            
            # PROD keys
            prod_keys_str = ', '.join(r.prod_key_set) if r.prod_key_set else "(none)"
            if len(prod_keys_str) > widths[3]:
                prod_keys_str = prod_keys_str[:widths[3]-3] + "..."
            row += self._cell_left(prod_keys_str, widths[3]) + self.VERTICAL
            
            # Status icon
            row += self._cell(r.status_icon, widths[4], self._status_color(r.status)) + self.VERTICAL
            
            lines.append(row)
        
        lines.append(self._hline_bottom(widths))
        
        # Legend
        lines.append("")
        lines.append(self._colorize("Legend: ", self.colors.BOLD) + 
                   f"{self._colorize('✅ same structure', self.colors.GREEN)}  " +
                   f"{self._colorize('⚠️ different', self.colors.YELLOW)}  " +
                   f"{self._colorize('❌ invalid/missing', self.colors.RED)}")
        
        return "\n".join(lines)
    
    def format_env_table_compact(self, results: List[EnvDiff]) -> str:
        """
        Format ENV comparison results as compact table with counts and key list.
        Shows counts + status, with detailed issues in summary.
        """
        if not results:
            return self._colorize("No ENV data found.", self.colors.YELLOW)
        
        # Sort: errors first, then different, then matched
        def sort_key(r: EnvDiff) -> tuple:
            status_order = {
                ComparisonStatus.INVALID: 0,
                ComparisonStatus.MISSING: 0,
                ComparisonStatus.DIFFERENT: 1,
                ComparisonStatus.UNSORTED: 1,
                ComparisonStatus.MATCHED: 2,
                ComparisonStatus.NA: 3,
            }
            return (status_order.get(r.status, 99), r.service)
        
        sorted_results = sorted(results, key=sort_key)
        
        # Column widths
        widths = [22, 6, 6, 6, 36]  # service, dev#, uat#, prod#, status
        
        # Header
        headers = ["Service", "DEV", "UAT", "PROD", "Status"]
        
        # Build table
        lines = []
        lines.append(self._colorize("\n=== ENV KEY COMPARISON ===", self.colors.BOLD + self.colors.CYAN))
        lines.append("")
        lines.append(self._hline(widths))
        
        # Header row
        header_row = self.VERTICAL
        for h, w in zip(headers, widths):
            header_row += self._header(h, w) + self.VERTICAL
        lines.append(header_row)
        lines.append(self._hline_mid(widths))
        
        # Data rows
        for r in sorted_results:
            row = self.VERTICAL
            
            # Service name
            row += self._cell_left(r.service, widths[0]) + self.VERTICAL
            
            # Key counts with color coding
            for count, w in zip([r.dev_keys, r.uat_keys, r.prod_keys], widths[1:4]):
                count_str = str(count) if count else "0"
                row += self._cell(count_str, w) + self.VERTICAL
            
            # Status with detailed issues
            status_parts = []
            if r.unique_to_dev:
                status_parts.append(f"+{len(r.unique_to_dev)}dev")
            if r.unique_to_uat:
                status_parts.append(f"+{len(r.unique_to_uat)}uat")
            if r.unique_to_prod:
                status_parts.append(f"+{len(r.unique_to_prod)}prod")
            if r.missing_in_dev:
                status_parts.append(f"-{len(r.missing_in_dev)}dev")
            if r.missing_in_uat:
                status_parts.append(f"-{len(r.missing_in_uat)}uat")
            if r.missing_in_prod:
                status_parts.append(f"-{len(r.missing_in_prod)}prod")
            if r.unsorted_in_dev or r.unsorted_in_uat or r.unsorted_in_prod:
                status_parts.append("unsorted")
            
            status_text = ', '.join(status_parts) if status_parts else "ok"
            if len(status_text) > widths[4]:
                status_text = status_text[:widths[4]-3] + "..."
            
            row += self._cell_left(status_text, widths[4], self._status_color(r.status)) + self.VERTICAL
            
            lines.append(row)
        
        lines.append(self._hline_bottom(widths))
        
        # Legend
        lines.append("")
        lines.append(self._colorize("Legend: ", self.colors.BOLD) + 
                   f"+N = unique keys only in that env  " +
                   f"-N = missing keys from that env\n" +
                   self._colorize("         ", self.colors.BOLD) + 
                   f"{self._colorize('✅ same structure', self.colors.GREEN)}  " +
                   f"{self._colorize('⚠️ different', self.colors.YELLOW)}  " +
                   f"{self._colorize('❌ invalid/missing', self.colors.RED)}")
        
        return "\n".join(lines)
    
    def format_env_output_for_fix(self, results: List[EnvDiff]) -> str:
        """
        Format ENV output for STANDARDIZATION AND FIX.
        Shows MISSING and DIFF only.
        Structure:
        - ENV SUMMARY (aggregate)
        - ENV DETAILS (service-by-service with one key per line)
        """
        if not results:
            return self._colorize("No ENV data found.", self.colors.YELLOW)
        
        lines = []
        
        # Collect stats
        services_with_issues = []
        total_missing_prod_vs_uat = 0
        total_missing_uat_vs_dev = 0
        
        for r in results:
            if r.status != ComparisonStatus.MATCHED:
                services_with_issues.append(r)
                total_missing_prod_vs_uat += len(r.missing_in_prod)
                total_missing_uat_vs_dev += len(r.missing_in_uat)
        
        # === ENV SUMMARY ===
        lines.append(self._colorize("\n=== ENV SUMMARY ===", self.colors.BOLD + self.colors.CYAN))
        lines.append(f"Services with issues: {len(services_with_issues)}")
        
        # Count aggregate issues
        all_missing_prod_vs_uat = set()
        all_missing_uat_vs_dev = set()
        all_unique_prod = set()
        all_unique_uat = set()
        all_unique_dev = set()
        
        for r in services_with_issues:
            all_missing_prod_vs_uat.update(r.missing_in_prod)
            all_missing_uat_vs_dev.update(r.missing_in_uat)
            all_unique_prod.update(r.unique_to_prod)
            all_unique_uat.update(r.unique_to_uat)
            all_unique_dev.update(r.unique_to_dev)
        
        if all_missing_prod_vs_uat:
            lines.append(f"  PROD diff from UAT: {len(all_missing_prod_vs_uat)} keys")
        if all_missing_uat_vs_dev:
            lines.append(f"  UAT diff from DEV: {len(all_missing_uat_vs_dev)} keys")
        if all_unique_prod or all_unique_uat or all_unique_dev:
            lines.append(f"  Unique keys: {len(all_unique_prod | all_unique_uat | all_unique_dev)} across all")
        
        if not services_with_issues:
            lines.append(self._colorize("\n✅ All services have same ENV structure!", self.colors.GREEN))
            return "\n".join(lines)
        
        # === ENV DETAILS ===
        lines.append(self._colorize("\n=== ENV DETAILS ===", self.colors.BOLD + self.colors.CYAN))
        
        # Sort: issues first
        def sort_key(r: EnvDiff) -> tuple:
            status_order = {
                ComparisonStatus.INVALID: 0,
                ComparisonStatus.MISSING: 0,
                ComparisonStatus.DIFFERENT: 1,
                ComparisonStatus.UNSORTED: 1,
                ComparisonStatus.MATCHED: 2,
                ComparisonStatus.NA: 3,
            }
            return (status_order.get(r.status, 99), r.service)
        
        sorted_results = sorted(results, key=sort_key)
        
        for r in sorted_results:
            lines.append("")
            lines.append(self._colorize(f"Service: {r.service}", self.colors.BOLD + self.colors.CYAN))
            
            has_issues = (r.missing_in_prod or r.missing_in_uat or 
                          r.unique_to_prod or r.unique_to_uat or r.unique_to_dev)
            
            if not has_issues:
                lines.append(f"  {self._colorize('✅ OK', self.colors.GREEN)}")
                continue
            
            # PROD diff from UAT
            if r.missing_in_prod or r.unique_to_prod:
                lines.append(self._colorize("  PROD diff from UAT:", self.colors.YELLOW))
                for key in r.missing_in_prod:
                    lines.append(f"    MISSING_IN_PROD: {key}")
                for key in r.unique_to_prod:
                    lines.append(f"    UNIQUE_IN_PROD: {key}")
            
            # UAT diff from DEV
            if r.missing_in_uat or r.unique_to_uat:
                lines.append(self._colorize("  UAT diff from DEV:", self.colors.YELLOW))
                for key in r.missing_in_uat:
                    lines.append(f"    MISSING_IN_UAT: {key}")
                for key in r.unique_to_uat:
                    lines.append(f"    UNIQUE_IN_UAT: {key}")
            
            # DEV unique (rarely needed but shown for completeness)
            if r.unique_to_dev:
                lines.append(self._colorize("  DEV unique:", self.colors.YELLOW))
                for key in r.unique_to_dev:
                    lines.append(f"    UNIQUE_IN_DEV: {key}")
        
        return "\n".join(lines)
    
    def format_detailed_env_issues(self, result: EnvDiff) -> str:
        """Format detailed ENV issues for a single service"""
        lines = []
        lines.append("")
        lines.append(self._colorize(f"--- {result.service} ---", self.colors.BOLD + self.colors.CYAN))
        
        if result.missing_in_dev:
            lines.append(f"  {self._colorize('Missing in dev:', self.colors.YELLOW)} {', '.join(result.missing_in_dev)}")
        if result.missing_in_uat:
            lines.append(f"  {self._colorize('Missing in uat:', self.colors.YELLOW)} {', '.join(result.missing_in_uat)}")
        if result.missing_in_prod:
            lines.append(f"  {self._colorize('Missing in prod:', self.colors.RED)} {', '.join(result.missing_in_prod)}")
        if result.unsorted_in_dev:
            lines.append(f"  {self._colorize('Unsorted in dev:', self.colors.YELLOW)} keys not alphabetically sorted")
        if result.unsorted_in_uat:
            lines.append(f"  {self._colorize('Unsorted in uat:', self.colors.YELLOW)} keys not alphabetically sorted")
        if result.unsorted_in_prod:
            lines.append(f"  {self._colorize('Unsorted in prod:', self.colors.YELLOW)} keys not alphabetically sorted")
        
        if not any([result.missing_in_dev, result.missing_in_uat, result.missing_in_prod,
                   result.unsorted_in_dev, result.unsorted_in_uat, result.unsorted_in_prod]):
            lines.append(f"  {self._colorize('✅ No issues found', self.colors.GREEN)}")
        
        return "\n".join(lines)
    
    def format_summary(self, resource_results: List[ResourceDiff], env_results: List[EnvDiff]) -> str:
        """Format summary of all results"""
        lines = []
        lines.append(self._colorize("\n" + "=" * 60, self.colors.BOLD + self.colors.CYAN))
        lines.append(self._colorize("SUMMARY", self.colors.BOLD + self.colors.CYAN))
        lines.append(self._colorize("=" * 60, self.colors.BOLD + self.colors.CYAN))
        
        # Resource summary
        total = len(resource_results)
        matched = sum(1 for r in resource_results if r.status == ComparisonStatus.MATCHED)
        different = sum(1 for r in resource_results if r.status == ComparisonStatus.DIFFERENT)
        invalid = sum(1 for r in resource_results if r.status in [ComparisonStatus.INVALID, ComparisonStatus.MISSING])
        
        lines.append(f"\nResources: {total} services")
        lines.append(f"  {self._colorize('✅', self.colors.GREEN)} Matched: {matched}")
        lines.append(f"  {self._colorize('⚠️', self.colors.YELLOW)} Different: {different}")
        lines.append(f"  {self._colorize('❌', self.colors.RED)} Invalid/Missing: {invalid}")
        
        # ENV summary
        total = len(env_results)
        matched = sum(1 for r in env_results if r.status == ComparisonStatus.MATCHED)
        different = sum(1 for r in env_results if r.status == ComparisonStatus.DIFFERENT)
        invalid = sum(1 for r in env_results if r.status in [ComparisonStatus.INVALID, ComparisonStatus.MISSING])
        unsorted = sum(1 for r in env_results if r.status == ComparisonStatus.UNSORTED)
        
        lines.append(f"\nENV Keys: {total} services")
        lines.append(f"  {self._colorize('✅', self.colors.GREEN)} Same structure: {matched}")
        lines.append(f"  {self._colorize('⚠️', self.colors.YELLOW)} Different: {different}")
        lines.append(f"  {self._colorize('❌', self.colors.RED)} Invalid: {invalid}")
        lines.append(f"  {self._colorize('⚠️', self.colors.YELLOW)} Unsorted: {unsorted}")
        
        # Aggregate key stats
        total_dev_keys = sum(r.dev_keys for r in env_results)
        total_uat_keys = sum(r.uat_keys for r in env_results)
        total_prod_keys = sum(r.prod_keys for r in env_results)
        
        lines.append(f"\nTotal ENV keys across all services:")
        lines.append(f"  DEV:  {total_dev_keys}")
        lines.append(f"  UAT:  {total_uat_keys}")
        lines.append(f"  PROD: {total_prod_keys}")
        
        # Services needing attention
        needs_attention = [r for r in env_results if r.status != ComparisonStatus.MATCHED]
        if needs_attention:
            lines.append(f"\n{self._colorize('Services needing attention:', self.colors.RED)} {len(needs_attention)}")
        
        return "\n".join(lines)

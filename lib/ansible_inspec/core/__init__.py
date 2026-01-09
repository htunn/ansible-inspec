"""
Core functionality for ansible-inspec

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ansible_inspec.ansible_adapter import AnsibleInventory, InventoryHost
from ansible_inspec.inspec_adapter import InSpecProfile, InSpecRunner, InSpecResult
from ansible_inspec.reporters import (
    InSpecJSONReport, InSpecProfile as ReportProfile, InSpecControl,
    InSpecStatistics, InSpecPlatform, get_default_output_path, parse_reporter_string
)


@dataclass
class ExecutionConfig:
    """Configuration for ansible-inspec execution"""
    profile_path: str
    inventory_path: Optional[str] = None
    target: Optional[str] = None
    group: Optional[str] = None
    host: Optional[str] = None
    reporter: str = 'cli'
    is_supermarket: bool = False  # Flag to indicate if profile is from Chef Supermarket
    output_path: Optional[str] = None
    sudo: bool = False
    parallel: bool = False
    max_workers: int = 5
    

@dataclass  
class ExecutionResult:
    """Results from ansible-inspec execution"""
    total_hosts: int
    successful_hosts: int
    failed_hosts: int
    host_results: Dict[str, InSpecResult] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if all hosts passed"""
        return self.failed_hosts == 0 and len(self.errors) == 0
    
    def summary(self) -> str:
        """Get execution summary"""
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status}: {self.successful_hosts}/{self.total_hosts} hosts passed"
    
    def to_json(self, profile_name: str = "ansible-inspec") -> str:
        """
        Export results to InSpec-compatible JSON format
        
        Args:
            profile_name: Name of the profile for report
            
        Returns:
            JSON string in InSpec schema format
        """
        report = InSpecJSONReport()
        
        # Aggregate all results
        all_controls = []
        total_duration = 0.0
        
        for host, result in self.host_results.items():
            # Convert each InSpecResult to controls
            for control in result.controls:
                control_dict = {
                    'id': control.get('id', 'unknown'),
                    'title': control.get('title'),
                    'desc': control.get('description'),
                    'impact': control.get('impact', 0.5),
                    'refs': control.get('refs', []),
                    'tags': control.get('tags', {}),
                    'code': control.get('code', ''),
                    'source_location': control.get('source_location', {}),
                    'results': control.get('results', [])
                }
                all_controls.append(control_dict)
            
            total_duration += result.duration
        
        # Create profile
        profile = ReportProfile(
            name=profile_name,
            version='1.0.0',
            sha256='',
            title=f'{profile_name} compliance checks',
            maintainer='ansible-inspec',
            summary=f'Aggregated results from {self.total_hosts} host(s)',
            license='GPL-3.0',
            copyright='ansible-inspec contributors',
            copyright_email='htunnthuthu.linux@gmail.com',
            supports=[],
            attributes=[],
            groups=[],
            controls=all_controls
        )
        
        report.profiles.append(profile)
        report.statistics = InSpecStatistics(duration=total_duration)
        
        # Add errors to report if any
        json_dict = report.to_dict()
        if self.errors:
            json_dict['errors'] = dict(self.errors)
        
        import json as json_module
        return json_module.dumps(json_dict, indent=2)
    
    def to_junit(self) -> str:
        """
        Export results to JUnit XML format
        
        Returns:
            JUnit XML string
        """
        from xml.etree import ElementTree as ET
        
        # Create root testsuite
        testsuite = ET.Element('testsuite', {
            'name': 'ansible-inspec',
            'tests': str(sum(r.total for r in self.host_results.values())),
            'failures': str(sum(r.failed for r in self.host_results.values())),
            'skipped': str(sum(r.skipped for r in self.host_results.values())),
            'time': str(sum(r.duration for r in self.host_results.values()))
        })
        
        # Add testcases for each host
        for host, result in self.host_results.items():
            for control in result.controls:
                testcase = ET.SubElement(testsuite, 'testcase', {
                    'name': f"{host}.{control.get('id', 'unknown')}",
                    'classname': host,
                    'time': str(control.get('duration', 0.0))
                })
                
                # Add failures
                for test_result in control.get('results', []):
                    if test_result.get('status') == 'failed':
                        failure = ET.SubElement(testcase, 'failure', {
                            'message': test_result.get('message', 'Test failed')
                        })
                        failure.text = test_result.get('backtrace', '')
        
        return ET.tostring(testsuite, encoding='unicode')
    
    def to_html(self, title: str = "Compliance Report") -> str:
        """
        Export results to HTML format
        
        Args:
            title: Report title
            
        Returns:
            HTML string
        """
        passed = sum(r.passed for r in self.host_results.values())
        failed = sum(r.failed for r in self.host_results.values())
        skipped = sum(r.skipped for r in self.host_results.values())
        total = sum(r.total for r in self.host_results.values())
        
        # Determine if there were execution errors vs test failures
        has_execution_errors = len(self.errors) > 0
        error_status = ""
        if has_execution_errors:
            error_status = '<p class="fail"><strong>⚠ Execution Errors:</strong> Some hosts failed to execute tests</p>'
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .pass {{ color: green; font-weight: bold; }}
        .fail {{ color: red; font-weight: bold; }}
        .skip {{ color: orange; font-weight: bold; }}
        .warning {{ color: orange; background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        pre {{ background: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="summary">
        <h2>Summary</h2>
        {error_status}
        <p><strong>Total Hosts:</strong> {self.total_hosts}</p>
        <p><strong>Successful Hosts:</strong> {self.successful_hosts}</p>
        <p><strong>Failed Hosts:</strong> {self.failed_hosts}</p>
        <p><strong>Total Tests:</strong> {total}</p>
        <p class="pass">Passed: {passed}</p>
        <p class="fail">Failed: {failed}</p>
        <p class="skip">Skipped: {skipped}</p>
    </div>
    
    <h2>Host Results</h2>
    <table>
        <tr>
            <th>Host</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Skipped</th>
            <th>Total</th>
            <th>Status</th>
        </tr>
"""
        
        for host, result in self.host_results.items():
            status_class = "pass" if result.passed == result.total else "fail"
            status = "PASS" if result.passed == result.total else "FAIL"
            html += f"""        <tr>
            <td>{host}</td>
            <td>{result.passed}</td>
            <td>{result.failed}</td>
            <td>{result.skipped}</td>
            <td>{result.total}</td>
            <td class="{status_class}">{status}</td>
        </tr>
"""
        
        html += """    </table>
"""
        
        # Add errors section if any
        if self.errors:
            html += """
    <h2>Execution Errors</h2>
    <div class="summary" style="background: #ffe6e6;">
"""
            for host, error in self.errors.items():
                html += f"""        <p class="fail"><strong>{host}:</strong></p>
        <pre>{error}</pre>
"""
            html += """    </div>
"""
        
        html += """    <p><em>Generated by ansible-inspec on {}</em></p>
</body>
</html>""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return html
    
    def save(self, path: str, format: str = 'json') -> None:
        """
        Save results to file in specified format
        
        Args:
            path: Output file path
            format: Output format (json, junit, html)
        """
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        
        if format == 'json':
            content = self.to_json()
        elif format == 'junit':
            content = self.to_junit()
        elif format == 'html':
            content = self.to_html()
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with open(path, 'w') as f:
            f.write(content)


class Config:
    """Configuration management for ansible-inspec"""
    
    def __init__(self):
        self.settings: Dict[str, Any] = {
            'reporter': 'cli',
            'sudo': False,
            'parallel': False,
            'max_workers': 5,
        }
    
    def load_from_file(self, config_path: str):
        """Load configuration from file"""
        import yaml
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
        
        self.settings.update(file_config)
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.settings[key] = value


class Runner:
    """Main execution engine for ansible-inspec"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def run(self, execution_config: ExecutionConfig) -> ExecutionResult:
        """
        Run InSpec profile against targets
        
        Args:
            execution_config: Configuration for this execution
            
        Returns:
            ExecutionResult with test results
        """
        # Load InSpec profile
        profile = InSpecProfile(
            execution_config.profile_path,
            is_supermarket=execution_config.is_supermarket
        )
        
        # Determine targets
        targets = self._get_targets(execution_config)
        
        if not targets:
            raise ValueError("No targets specified. Provide inventory, target, or run locally.")
        
        # Execute tests against targets
        result = ExecutionResult(
            total_hosts=len(targets),
            successful_hosts=0,
            failed_hosts=0
        )
        
        for target in targets:
            try:
                # Run InSpec against this target
                runner = InSpecRunner(profile, target.get('uri'))
                test_result = runner.execute(reporter=execution_config.reporter)
                
                # Store result
                host_name = target.get('name', target.get('uri'))
                result.host_results[host_name] = test_result
                
                if test_result.success:
                    result.successful_hosts += 1
                else:
                    result.failed_hosts += 1
                    
            except Exception as e:
                host_name = target.get('name', target.get('uri'))
                result.errors[host_name] = str(e)
                result.failed_hosts += 1
        
        return result
    
    def _get_targets(self, config: ExecutionConfig) -> List[Dict[str, str]]:
        """
        Determine targets from configuration
        
        Args:
            config: Execution configuration
            
        Returns:
            List of target dictionaries with 'name' and 'uri'
        """
        targets = []
        
        # Option 1: Ansible inventory
        if config.inventory_path:
            inventory = AnsibleInventory(config.inventory_path)
            
            # Filter by group or host if specified
            if config.host:
                host = inventory.get_host(config.host)
                if host:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
            elif config.group:
                hosts = inventory.get_hosts(config.group)
                for host in hosts:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
            else:
                # All hosts
                hosts = inventory.get_hosts()
                for host in hosts:
                    targets.append({
                        'name': host.name,
                        'uri': host.get_connection_uri()
                    })
        
        # Option 2: Direct target URI
        elif config.target:
            targets.append({
                'name': config.target,
                'uri': config.target
            })
        
        # Option 3: Local execution
        else:
            targets.append({
                'name': 'localhost',
                'uri': 'local://'
            })
        
        return targets
    
    def validate_profile(self, profile_path: str) -> bool:
        """
        Validate an InSpec profile
        
        Args:
            profile_path: Path to profile
            
        Returns:
            True if valid
        """
        try:
            profile = InSpecProfile(profile_path)
            return profile.validate()
        except Exception:
            return False


__all__ = ['Config', 'Runner', 'ExecutionConfig', 'ExecutionResult']

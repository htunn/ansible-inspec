"""
Ansible Callback Plugin for InSpec-Compatible Compliance Reporting

This callback plugin tracks task execution results from converted Ansible
collections and generates InSpec JSON schema-compatible compliance reports.

USAGE:
    Enable in ansible.cfg:
        [defaults]
        callbacks_enabled = compliance_reporter
        callback_result_dir = .compliance-reports

    Or via environment variable:
        export ANSIBLE_CALLBACKS_ENABLED=compliance_reporter
        export ANSIBLE_CALLBACK_RESULT_DIR=.compliance-reports

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: compliance_reporter
    type: aggregate
    short_description: Generate InSpec-compatible compliance reports
    version_added: "0.1.0"
    description:
        - This callback plugin generates InSpec JSON schema-compatible reports
        - Tracks task results from converted InSpec profiles
        - Maps Ansible task assertions to InSpec control/test structure
        - Saves reports to .compliance-reports/ directory
    requirements:
        - enable in configuration file or via ANSIBLE_CALLBACKS_ENABLED
    options:
      output_dir:
        name: Output directory for reports
        default: .compliance-reports
        description: Directory where compliance reports will be saved
        env:
          - name: ANSIBLE_CALLBACK_RESULT_DIR
        ini:
          - section: callback_compliance_reporter
            key: output_dir
      output_format:
        name: Output format
        default: json
        description: Report format (json, html, junit)
        env:
          - name: ANSIBLE_COMPLIANCE_FORMAT
        ini:
          - section: callback_compliance_reporter
            key: output_format
        choices: ['json', 'html', 'junit']
'''

import os
import json
import hashlib
from datetime import datetime
from collections import defaultdict
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    Callback plugin for InSpec-compatible compliance reporting
    """
    
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'compliance_reporter'
    CALLBACK_NEEDS_ENABLED = True
    
    def __init__(self):
        super(CallbackModule, self).__init__()
        
        self.results = defaultdict(lambda: {
            'controls': [],
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        })
        
        self.start_time = None
        self.end_time = None
        self.playbook_name = None
        self.profile_name = 'ansible-inspec'
    
    def v2_playbook_on_start(self, playbook):
        """Called when playbook starts"""
        self.start_time = datetime.now()
        self.playbook_name = os.path.basename(playbook._file_name)
        
        # Extract profile name from playbook path if in collection
        if 'ansible_collections' in playbook._file_name:
            parts = playbook._file_name.split('ansible_collections/')
            if len(parts) > 1:
                collection_parts = parts[1].split('/')
                if len(collection_parts) >= 2:
                    self.profile_name = f"{collection_parts[0]}.{collection_parts[1]}"
        
        if not self.profile_name:
            self.profile_name = 'ansible-inspec'
    
    def v2_playbook_on_task_start(self, task, is_conditional):
        """Called when task starts"""
        pass
    
    def v2_runner_on_ok(self, result):
        """Called when task succeeds"""
        self._process_result(result, 'passed')
    
    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Called when task fails"""
        self._process_result(result, 'failed' if not ignore_errors else 'passed')
    
    def v2_runner_on_skipped(self, result):
        """Called when task is skipped"""
        self._process_result(result, 'skipped')
    
    def _process_result(self, result, status):
        """Process task result and extract compliance data"""
        host = result._host.get_name()
        task = result._task
        task_name = task.get_name()
        
        # Only process compliance-related tasks
        # Look for tasks with compliance tags or assert modules
        is_compliance_task = (
            'compliance' in task.tags or
            'assert' in task.action or
            task_name.startswith('Check ') or
            task_name.startswith('Verify ') or
            task_name.startswith('Ensure ')
        )
        
        if not is_compliance_task:
            return
        
        # Extract control ID from task name or tags
        control_id = self._extract_control_id(task_name, task.tags)
        
        # Build control result
        control = {
            'id': control_id,
            'title': task_name,
            'desc': task_name,
            'impact': 0.7,  # Default impact
            'refs': [],
            'tags': {tag: True for tag in task.tags},
            'code': '',
            'source_location': {
                'ref': task._parent._play._ds.get('name', ''),
                'line': 0
            },
            'results': [{
                'status': status,
                'code_desc': task_name,
                'run_time': 0.0,
                'start_time': datetime.now().isoformat()
            }]
        }
        
        # Add failure details if failed
        if status == 'failed':
            control['results'][0]['message'] = result._result.get('msg', 'Task failed')
            if 'exception' in result._result:
                control['results'][0]['backtrace'] = result._result['exception']
        
        # Add to results
        self.results[host]['controls'].append(control)
        self.results[host]['total'] += 1
        
        if status == 'passed':
            self.results[host]['passed'] += 1
        elif status == 'failed':
            self.results[host]['failed'] += 1
        elif status == 'skipped':
            self.results[host]['skipped'] += 1
    
    def _extract_control_id(self, task_name, tags):
        """Extract or generate control ID from task"""
        # Check for control tag
        for tag in tags:
            if tag.startswith('control-'):
                return tag.replace('control-', '')
        
        # Generate from task name
        clean_name = task_name.lower().replace(' ', '-')
        return hashlib.md5(clean_name.encode()).hexdigest()[:12]
    
    def v2_playbook_on_stats(self, stats):
        """Called when playbook ends - generate report"""
        self.end_time = datetime.now()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = 0.0
        
        # Build InSpec-compatible report
        report = self._build_inspec_report(duration, stats)
        
        # Save report
        self._save_report(report)
    
    def _build_inspec_report(self, duration, stats):
        """Build InSpec JSON schema-compatible report"""
        # Aggregate controls from all hosts
        all_controls = []
        for host, host_data in self.results.items():
            all_controls.extend(host_data['controls'])
        
        # Calculate profile statistics
        total_passed = sum(h['passed'] for h in self.results.values())
        total_failed = sum(h['failed'] for h in self.results.values())
        total_skipped = sum(h['skipped'] for h in self.results.values())
        
        # Build profile
        profile = {
            'name': self.profile_name,
            'version': '1.0.0',
            'sha256': hashlib.sha256(self.profile_name.encode()).hexdigest(),
            'title': f'{self.profile_name} compliance checks',
            'maintainer': 'ansible-inspec',
            'summary': f'Converted Ansible collection compliance checks',
            'license': 'GPL-3.0',
            'copyright': 'ansible-inspec contributors',
            'copyright_email': 'htunnthuthu.linux@gmail.com',
            'supports': [],
            'attributes': [],
            'groups': [],
            'controls': all_controls,
            'status': 'loaded'
        }
        
        # Build complete report
        report = {
            'platform': {
                'name': 'ansible',
                'release': '2.9+',
                'target_id': ','.join(self.results.keys())
            },
            'profiles': [profile],
            'statistics': {
                'duration': duration,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'total': total_passed + total_failed + total_skipped
            },
            'version': '5.22.0'
        }
        
        return report
    
    def _save_report(self, report):
        """Save report to file"""
        # Get output directory from config
        output_dir = self.get_option('output_dir') or '.compliance-reports'
        output_format = self.get_option('output_format') or 'json'
        
        # Create directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{self.profile_name}-{self.playbook_name}.{output_format}"
        filepath = os.path.join(output_dir, filename)
        
        # Save based on format
        if output_format == 'json':
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
        elif output_format == 'html':
            html_content = self._generate_html_report(report)
            with open(filepath, 'w') as f:
                f.write(html_content)
        elif output_format == 'junit':
            junit_content = self._generate_junit_report(report)
            filepath = filepath.replace('.junit', '.xml')
            with open(filepath, 'w') as f:
                f.write(junit_content)
        
        self._display.display(f"Compliance report saved: {filepath}", color='bright green')
    
    def _generate_html_report(self, report):
        """Generate HTML report from InSpec data"""
        stats = report['statistics']
        profile = report['profiles'][0]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Report - {profile['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .pass {{ color: green; font-weight: bold; }}
        .fail {{ color: red; font-weight: bold; }}
        .skip {{ color: orange; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Compliance Report: {profile['name']}</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {stats['total']}</p>
        <p class="pass">Passed: {stats['passed']}</p>
        <p class="fail">Failed: {stats['failed']}</p>
        <p class="skip">Skipped: {stats['skipped']}</p>
        <p><strong>Duration:</strong> {stats['duration']:.2f}s</p>
    </div>
    
    <h2>Controls</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
        </tr>
"""
        
        for control in profile['controls']:
            status = control['results'][0]['status'] if control['results'] else 'unknown'
            status_class = 'pass' if status == 'passed' else ('fail' if status == 'failed' else 'skip')
            html += f"""        <tr>
            <td>{control['id']}</td>
            <td>{control['title']}</td>
            <td class="{status_class}">{status.upper()}</td>
        </tr>
"""
        
        html += f"""    </table>
    <p><em>Generated by ansible-inspec on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
</body>
</html>"""
        
        return html
    
    def _generate_junit_report(self, report):
        """Generate JUnit XML report from InSpec data"""
        from xml.etree import ElementTree as ET
        
        stats = report['statistics']
        profile = report['profiles'][0]
        
        testsuite = ET.Element('testsuite', {
            'name': profile['name'],
            'tests': str(stats['total']),
            'failures': str(stats['failed']),
            'skipped': str(stats['skipped']),
            'time': str(stats['duration'])
        })
        
        for control in profile['controls']:
            testcase = ET.SubElement(testsuite, 'testcase', {
                'name': control['id'],
                'classname': profile['name'],
                'time': '0'
            })
            
            if control['results']:
                result = control['results'][0]
                if result['status'] == 'failed':
                    failure = ET.SubElement(testcase, 'failure', {
                        'message': result.get('message', 'Test failed')
                    })
                    failure.text = result.get('backtrace', '')
                elif result['status'] == 'skipped':
                    ET.SubElement(testcase, 'skipped')
        
        return ET.tostring(testsuite, encoding='unicode')

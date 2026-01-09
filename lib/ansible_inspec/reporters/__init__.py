"""
InSpec-compatible reporters for ansible-inspec

This module provides InSpec JSON schema-compatible reporting functionality
for both native InSpec profile execution and converted Ansible collections.

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


# InSpec JSON Schema v4 structure
# Based on https://docs.chef.io/inspec/reporters/#json

@dataclass
class InSpecControl:
    """InSpec control result structure"""
    id: str
    title: Optional[str]
    desc: Optional[str]
    impact: float
    refs: List[Dict[str, Any]]
    tags: Dict[str, Any]
    code: str
    source_location: Dict[str, Any]
    results: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to InSpec JSON schema format"""
        return {
            'id': self.id,
            'title': self.title,
            'desc': self.desc,
            'impact': self.impact,
            'refs': self.refs,
            'tags': self.tags,
            'code': self.code,
            'source_location': self.source_location,
            'results': self.results
        }


@dataclass
class InSpecProfile:
    """InSpec profile metadata structure"""
    name: str
    version: str
    sha256: str
    title: Optional[str]
    maintainer: Optional[str]
    summary: Optional[str]
    license: Optional[str]
    copyright: Optional[str]
    copyright_email: Optional[str]
    supports: List[Dict[str, Any]]
    attributes: List[Dict[str, Any]]
    groups: List[Dict[str, Any]]
    controls: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to InSpec JSON schema format"""
        return {
            'name': self.name,
            'version': self.version,
            'sha256': self.sha256,
            'title': self.title,
            'maintainer': self.maintainer,
            'summary': self.summary,
            'license': self.license,
            'copyright': self.copyright,
            'copyright_email': self.copyright_email,
            'supports': self.supports,
            'attributes': self.attributes,
            'groups': self.groups,
            'controls': self.controls
        }


@dataclass
class InSpecStatistics:
    """InSpec execution statistics"""
    duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to InSpec JSON schema format"""
        return {'duration': self.duration}


@dataclass
class InSpecPlatform:
    """Target platform information"""
    name: str
    release: str
    target_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to InSpec JSON schema format"""
        result = {
            'name': self.name,
            'release': self.release
        }
        if self.target_id:
            result['target_id'] = self.target_id
        return result


class InSpecJSONReport:
    """
    Generates InSpec JSON schema-compatible reports
    
    This class ensures 100% compatibility with InSpec's JSON reporter format,
    allowing seamless integration with Chef Automate, CI/CD pipelines, and
    other InSpec tooling.
    """
    
    def __init__(self, version: str = "5.22.0"):
        """
        Initialize report generator
        
        Args:
            version: InSpec version to report (for compatibility)
        """
        self.version = version
        self.profiles: List[InSpecProfile] = []
        self.platform: Optional[InSpecPlatform] = None
        self.statistics: Optional[InSpecStatistics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Generate complete InSpec JSON report
        
        Returns:
            Dictionary matching InSpec JSON schema v4
        """
        report = {
            'platform': self.platform.to_dict() if self.platform else {},
            'profiles': [profile.to_dict() for profile in self.profiles],
            'statistics': self.statistics.to_dict() if self.statistics else {'duration': 0.0},
            'version': self.version
        }
        return report
    
    def to_json(self, indent: int = 2) -> str:
        """
        Generate JSON string
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string matching InSpec format
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, path: str, indent: int = 2) -> None:
        """
        Save report to file
        
        Args:
            path: Output file path
            indent: JSON indentation level
        """
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json(indent=indent))


def get_default_output_path(reporter: str, profile_name: str = "profile") -> str:
    """
    Generate default output path following .compliance-reports/ convention
    
    Args:
        reporter: Reporter format (json, yaml, html, junit)
        profile_name: Name of profile being executed
        
    Returns:
        Default output path
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Map reporter to file extension
    extensions = {
        'json': 'json',
        'json-min': 'json',
        'json-rspec': 'json',
        'json-automate': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'html': 'html',
        'html2': 'html',
        'junit': 'xml',
        'junit2': 'xml',
    }
    
    ext = extensions.get(reporter.lower(), 'txt')
    filename = f"{timestamp}-{profile_name}-{reporter}.{ext}"
    
    return os.path.join('.compliance-reports', filename)


def parse_reporter_string(reporter_string: str) -> List[Dict[str, str]]:
    """
    Parse InSpec-style reporter string
    
    Supports formats like:
    - "cli"
    - "json"
    - "cli json:/tmp/report.json"
    - "json yaml:/tmp/report.yaml html:/tmp/report.html"
    
    Args:
        reporter_string: Reporter specification string
        
    Returns:
        List of reporter configurations with 'format' and optional 'path'
    """
    reporters = []
    parts = reporter_string.split()
    
    for part in parts:
        if ':' in part:
            # Format with path: "json:/tmp/report.json"
            format_name, path = part.split(':', 1)
            reporters.append({'format': format_name, 'path': path})
        else:
            # Format only: "cli"
            reporters.append({'format': part, 'path': None})
    
    return reporters


__all__ = [
    'InSpecControl',
    'InSpecProfile',
    'InSpecStatistics',
    'InSpecPlatform',
    'InSpecJSONReport',
    'get_default_output_path',
    'parse_reporter_string'
]

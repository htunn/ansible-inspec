"""
Streamlit UI for InSpec Execution Server

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

Provides a modern web UI for managing InSpec job templates and executions.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Configure page
st.set_page_config(
    page_title="InSpec Execution Server",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Base URL
API_BASE = "http://localhost:8080/api/v1"

def get_statistics():
    """Get server statistics"""
    try:
        response = requests.get(f"{API_BASE}/statistics/")
        return response.json()
    except:
        return {}

def get_jobs():
    """Get all jobs"""
    try:
        response = requests.get(f"{API_BASE}/jobs/")
        return response.json().get('results', [])
    except:
        return []

def get_job_templates():
    """Get all job templates"""
    try:
        response = requests.get(f"{API_BASE}/job_templates/")
        return response.json().get('results', [])
    except:
        return []

def launch_job(template_id, extra_vars=None):
    """Launch a job from template"""
    try:
        payload = {"extra_vars": extra_vars or {}}
        response = requests.post(
            f"{API_BASE}/job_templates/{template_id}/launch/",
            json=payload
        )
        return response.status_code == 201
    except:
        return False

def create_job_template(template_data):
    """Create a new job template"""
    try:
        response = requests.post(
            f"{API_BASE}/job_templates/",
            json=template_data
        )
        return response.status_code == 201
    except:
        return False

def update_job_template(template_id, template_data):
    """Update an existing job template"""
    try:
        response = requests.put(
            f"{API_BASE}/job_templates/{template_id}/",
            json=template_data
        )
        return response.status_code == 200
    except:
        return False

def delete_job_template(template_id):
    """Delete a job template"""
    try:
        response = requests.delete(f"{API_BASE}/job_templates/{template_id}/")
        return response.status_code == 204
    except:
        return False

def get_job_logs(job_id, lines=100):
    """Get live job logs from files"""
    try:
        response = requests.get(f"{API_BASE}/jobs/{job_id}/logs/", params={'lines': lines})
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .success-status {
        color: #28a745;
        font-weight: bold;
    }
    .failed-status {
        color: #dc3545;
        font-weight: bold;
    }
    .running-status {
        color: #17a2b8;
        font-weight: bold;
    }
    .pending-status {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔒 InSpec Execution Server")
st.markdown("**Web UI and REST API for ansible-inspec compliance testing**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["📊 Dashboard", "📋 Jobs", "📝 Job Templates", "➕ Create Template", "📚 API Docs"]
    )
    
    st.markdown("---")
    st.markdown("### Quick Links")
    st.markdown(f"[📖 API Documentation](http://localhost:8080/docs)")
    st.markdown(f"[📘 ReDoc](http://localhost:8080/redoc)")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)

# Dashboard Page
if page == "📊 Dashboard":
    st.header("Dashboard")
    
    # Get statistics
    stats = get_statistics()
    
    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Job Templates",
            stats.get('job_templates', 0),
            help="Total number of job templates"
        )
    
    with col2:
        st.metric(
            "Total Jobs",
            stats.get('total_jobs', 0),
            help="Total number of jobs executed"
        )
    
    with col3:
        st.metric(
            "Successful",
            stats.get('successful_jobs', 0),
            delta=None,
            help="Successfully completed jobs"
        )
    
    with col4:
        st.metric(
            "Failed",
            stats.get('failed_jobs', 0),
            delta=None,
            help="Failed jobs"
        )
    
    with col5:
        success_rate = stats.get('success_rate', 0)
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            help="Percentage of successful jobs"
        )
    
    st.markdown("---")
    
    # Recent jobs
    st.subheader("Recent Jobs")
    jobs = get_jobs()
    
    if jobs:
        recent_jobs = jobs[:10]  # Show last 10 jobs
        
        df = pd.DataFrame([{
            'Template': job['job_template_name'],
            'Status': job['status'],
            'Created': datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S'),
            'ID': job['id'][:8]
        } for job in recent_jobs])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No jobs found")

# Jobs Page
elif page == "📋 Jobs":
    st.header("Jobs")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "running", "successful", "failed", "canceled"]
        )
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    jobs = get_jobs()
    
    if status_filter != "All":
        jobs = [j for j in jobs if j['status'] == status_filter]
    
    if jobs:
        for job in jobs:
            with st.expander(
                f"{'✅' if job['status'] == 'successful' else '❌' if job['status'] == 'failed' else '🔄' if job['status'] == 'running' else '⏸️'} "
                f"{job['job_template_name']} - {job['status'].upper()}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Job ID:** `{job['id']}`")
                    st.write(f"**Template:** {job['job_template_name']}")
                    st.write(f"**Status:** {job['status']}")
                
                with col2:
                    st.write(f"**Created:** {datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                    if job.get('started_at'):
                        st.write(f"**Started:** {datetime.fromisoformat(job['started_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                    if job.get('finished_at'):
                        st.write(f"**Finished:** {datetime.fromisoformat(job['finished_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Add delete button for pending jobs
                if job['status'] == 'pending':
                    if st.button(f"🗑️ Delete", key=f"delete_{job['id']}", type="secondary"):
                        response = requests.delete(f"{API_BASE}/jobs/{job['id']}/")
                        if response.status_code == 200:
                            st.success(f"Job {job['id'][:8]} deleted")
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_msg = response.json().get('detail', 'Unknown error')
                            st.error(f"Failed to delete job: {error_msg}")
                
                # Show live logs for running jobs
                if job['status'] == 'running':
                    st.markdown("**🔴 Live Output:**")
                    logs = get_job_logs(job['id'], lines=50)
                    
                    if logs and logs.get('has_output'):
                        tab1, tab2 = st.tabs(["stdout", "stderr"])
                        
                        with tab1:
                            if logs.get('stdout'):
                                st.code(logs['stdout'], language='bash')
                            else:
                                st.info("No output yet...")
                        
                        with tab2:
                            if logs.get('stderr'):
                                st.code(logs['stderr'], language='bash')
                            else:
                                st.info("No errors")
                    else:
                        st.info("⏳ Job is running, waiting for output...")
                    
                    # Auto-refresh for running jobs
                    if auto_refresh:
                        time.sleep(2)
                        st.rerun()
                
                # Show final output for completed jobs
                elif job.get('stdout') or job.get('stderr'):
                    tab1, tab2 = st.tabs(["stdout", "stderr"])
                    
                    with tab1:
                        if job.get('stdout'):
                            st.text_area("Output", job['stdout'], height=200, key=f"stdout_{job['id']}")
                        else:
                            st.info("No output")
                    
                    with tab2:
                        if job.get('stderr'):
                            st.text_area("Errors", job['stderr'], height=200, key=f"stderr_{job['id']}")
                        else:
                            st.info("No errors")
    else:
        st.info("No jobs found")

# Job Templates Page
elif page == "📝 Job Templates":
    st.header("Job Templates")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    templates = get_job_templates()
    
    if templates:
        for template in templates:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(template['name'])
                    st.write(template.get('description', 'No description'))
                    
                    # Show profile_path or playbook
                    if template.get('playbook'):
                        st.caption(f"Playbook: `{template['playbook']}`")
                    elif template.get('profile_path'):
                        st.caption(f"Profile: `{template['profile_path']}`")
                    
                    if template.get('inventory'):
                        st.caption(f"Inventory: `{template['inventory']}`")
                
                with col2:
                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("🚀", key=f"launch_{template['id']}", help="Launch job"):
                            if launch_job(template['id']):
                                st.success("Job launched!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to launch job")
                    with btn_col2:
                        edit_key = f"edit_{template['id']}"
                        if edit_key not in st.session_state:
                            st.session_state[edit_key] = False
                        if st.button("✏️", key=f"edit_btn_{template['id']}", help="Edit template"):
                            st.session_state[edit_key] = not st.session_state[edit_key]
                            st.rerun()
                    with btn_col3:
                        delete_key = f"confirm_delete_{template['id']}"
                        if delete_key not in st.session_state:
                            st.session_state[delete_key] = False
                        
                        if st.session_state[delete_key]:
                            # Show confirmation
                            if st.button("✅", key=f"confirm_yes_{template['id']}", help="Confirm delete"):
                                try:
                                    response = requests.delete(f"{API_BASE}/job_templates/{template['id']}/")
                                    if response.status_code == 204:
                                        st.success(f"Template '{template['name']}' deleted")
                                        st.session_state[delete_key] = False
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        error_detail = response.json().get('detail', 'Unknown error') if response.text else f"HTTP {response.status_code}"
                                        st.error(f"Failed to delete: {error_detail}")
                                        st.session_state[delete_key] = False
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    st.session_state[delete_key] = False
                        else:
                            if st.button("🗑️", key=f"delete_{template['id']}", help="Delete template", type="secondary"):
                                st.session_state[delete_key] = True
                                st.rerun()
                
                # Show edit form if edit mode is active
                edit_key = f"edit_{template['id']}"
                if st.session_state.get(edit_key, False):
                    with st.expander("✏️ Edit Template", expanded=True):
                        with st.form(key=f"edit_form_{template['id']}"):
                            new_name = st.text_input("Template Name", value=template['name'])
                            new_description = st.text_area("Description", value=template.get('description', ''))
                            
                            # Determine current mode
                            current_playbook_mode = bool(template.get('playbook'))
                            new_profile_path = st.text_input(
                                "Profile Path / Playbook",
                                value=template.get('playbook') or template.get('profile_path') or ''
                            )
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                new_profile_mode = st.checkbox("Use InSpec Profile", value=not current_playbook_mode)
                            with col_b:
                                new_playbook_mode = st.checkbox("Use Ansible Playbook", value=current_playbook_mode)
                            
                            new_inventory = st.text_input("Inventory File", value=template.get('inventory') or '')
                            new_target = st.text_input("Target", value=template.get('target') or '')
                            
                            # Environment variables
                            env_vars_dict = template.get('extra_vars', {}).get('env_vars', {})
                            
                            # Detect if values contain newlines or complex data
                            has_complex_values = any('\n' in str(v) or len(str(v)) > 100 for v in env_vars_dict.values()) if env_vars_dict else False
                            default_format = "JSON" if has_complex_values else "Simple (KEY=value)"
                            
                            new_env_format = st.radio(
                                "Format",
                                ["Simple (KEY=value)", "JSON"],
                                index=0 if default_format == "Simple (KEY=value)" else 1,
                                horizontal=True,
                                help="Choose format: Simple for basic values, JSON for complex/multi-line data"
                            )
                            
                            if new_env_format == "Simple (KEY=value)":
                                env_vars_str = '\n'.join([f"{k}={v}" for k, v in env_vars_dict.items()]) if env_vars_dict else ''
                                new_env_vars_text = st.text_area(
                                    "Environment Variables",
                                    value=env_vars_str,
                                    help="Format: KEY=value (one per line)"
                                )
                            else:
                                import json
                                env_vars_str = json.dumps(env_vars_dict, indent=2) if env_vars_dict else '{}'
                                new_env_vars_text = st.text_area(
                                    "Environment Variables (JSON)",
                                    value=env_vars_str,
                                    height=200,
                                    help="JSON format supports multi-line values"
                                )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    # Parse environment variables
                                    new_env_vars = {}
                                    if new_env_vars_text:
                                        if new_env_format == "JSON":
                                            try:
                                                import json
                                                new_env_vars = json.loads(new_env_vars_text)
                                                if not isinstance(new_env_vars, dict):
                                                    st.error("JSON must be an object/dictionary")
                                                    new_env_vars = {}
                                            except json.JSONDecodeError as e:
                                                st.error(f"Invalid JSON: {e}")
                                                new_env_vars = {}
                                        else:
                                            for line in new_env_vars_text.strip().split('\n'):
                                                if '=' in line:
                                                    key, value = line.split('=', 1)
                                                    new_env_vars[key.strip()] = value.strip()
                                    
                                    updated_template = {
                                        "name": new_name,
                                        "description": new_description,
                                        "inventory": new_inventory if new_inventory else None,
                                        "target": new_target if new_target else None,
                                        "extra_vars": {"env_vars": new_env_vars} if new_env_vars else {},
                                    }
                                    
                                    # Set profile_path or playbook based on mode
                                    if new_playbook_mode and new_profile_path:
                                        updated_template["playbook"] = new_profile_path
                                        updated_template["profile_path"] = None
                                    elif new_profile_path:
                                        updated_template["profile_path"] = new_profile_path
                                        updated_template["playbook"] = None
                                    else:
                                        updated_template["profile_path"] = None
                                        updated_template["playbook"] = None
                                    
                                    if update_job_template(template['id'], updated_template):
                                        st.success("Template updated successfully!")
                                        st.session_state[edit_key] = False
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to update template")
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state[edit_key] = False
                                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No job templates found. Create one to get started!")

# Create Template Page
elif page == "➕ Create Template":
    st.header("Create New Job Template")
    
    with st.form("create_template_form"):
        name = st.text_input("Template Name *", placeholder="My Compliance Check")
        description = st.text_area("Description", placeholder="Description of this template")
        
        col1, col2 = st.columns(2)
        
        with col1:
            profile_path = st.text_input(
                "Profile Path / Playbook",
                placeholder="/path/to/profile OR playbook.yml"
            )
            
            col2a, col2b = st.columns(2)
            with col2a:
                profile_mode = st.checkbox("Use InSpec Profile", value=True)
            with col2b:
                playbook_mode = st.checkbox("Use Ansible Playbook", value=False)
            
            inventory = st.text_input("Inventory File", placeholder="/path/to/inventory.yml")
            target = st.text_input(
                "Target",
                placeholder="ssh://user@host or docker://container (InSpec mode)"
            )
        
        with col2:
            reporter = st.text_input("Reporter", value="cli json", help="InSpec reporter format (InSpec mode only)")
            job_type = st.selectbox("Job Type", ["run", "check", "scan"])
            supermarket = st.checkbox("Load from Chef Supermarket", help="InSpec mode only")
            
        # Advanced options for Ansible playbooks
        st.subheader("Advanced Options")
        
        col3, col4 = st.columns(2)
        with col3:
            tags = st.text_input("Tags", placeholder="tag1,tag2,tag3")
            skip_tags = st.text_input("Skip Tags", placeholder="skip1,skip2")
            limit = st.text_input("Limit Hosts", placeholder="host1,host2")
            
        with col4:
            forks = st.number_input("Forks", min_value=1, max_value=50, value=5, help="Number of parallel processes")
            timeout = st.number_input("Timeout (seconds)", min_value=0, value=0, help="0 = no timeout")
            verbosity = st.slider("Verbosity", min_value=0, max_value=4, value=0)
            
        col5, col6 = st.columns(2)
        with col5:
            diff_mode = st.checkbox("Diff Mode", help="Show differences when changes are made")
            allow_simultaneous = st.checkbox("Allow Simultaneous", help="Allow concurrent executions")
        with col6:
            use_fact_cache = st.checkbox("Use Fact Cache")
            job_slice_count = st.number_input("Job Slice Count", min_value=1, value=1, help="Parallel job slicing")
        
        # Environment Variables Section
        st.subheader("Environment Variables")
        
        env_format = st.radio(
            "Format",
            ["Simple (KEY=value)", "JSON"],
            horizontal=True,
            help="Choose format: Simple for basic values, JSON for complex/multi-line data like certificates"
        )
        
        if env_format == "Simple (KEY=value)":
            st.markdown("Set environment variables (one per line, format: `KEY=value`)")
            env_vars_text = st.text_area(
                "Environment Variables",
                placeholder="CHECK_SSH=true\nMIN_DISK_SPACE_GB=20\nREQUIRED_PACKAGES=vim,curl,git",
                height=150,
                help="Environment variables will be available to the playbook via lookup('env', 'VAR_NAME')"
            )
        else:
            st.markdown("Set environment variables in JSON format (supports multi-line values)")
            env_vars_text = st.text_area(
                "Environment Variables (JSON)",
                placeholder='{\n  "CHECK_SSH": "true",\n  "CERT_CSR": "-----BEGIN CERTIFICATE REQUEST-----\\nMIIC...\\n-----END CERTIFICATE REQUEST-----",\n  "CONFIG_JSON": "{\\"key\\": \\"value\\"}",\n  "SCRIPT": "#!/bin/bash\\necho test"\n}',
                height=200,
                help="Use JSON format for complex values. Supports multi-line strings with \\n escape sequences"
            )
        
        submitted = st.form_submit_button("Create Template", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("Template name is required!")
            else:
                # Parse tags and skip_tags
                tags_list = [t.strip() for t in tags.split(',')] if tags else []
                skip_tags_list = [t.strip() for t in skip_tags.split(',')] if skip_tags else []
                
                # Parse environment variables
                env_vars = {}
                if env_vars_text:
                    if env_format == "JSON":
                        try:
                            import json
                            env_vars = json.loads(env_vars_text)
                            if not isinstance(env_vars, dict):
                                st.error("JSON must be an object/dictionary")
                                env_vars = {}
                        except json.JSONDecodeError as e:
                            st.error(f"Invalid JSON: {e}")
                            env_vars = {}
                    else:
                        for line in env_vars_text.strip().split('\n'):
                            line = line.strip()
                            if line and '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()
                
                template_data = {
                    "name": name,
                    "description": description,
                    "job_type": job_type,
                    "reporter": reporter if profile_mode else "cli json",
                    "supermarket": supermarket if profile_mode else False,
                    "inventory": inventory if inventory else None,
                    "target": target if target else None,
                    "tags": tags_list,
                    "skip_tags": skip_tags_list,
                    "limit": limit if limit else None,
                    "forks": forks,
                    "timeout": timeout,
                    "verbosity": verbosity,
                    "diff_mode": diff_mode,
                    "allow_simultaneous": allow_simultaneous,
                    "use_fact_cache": use_fact_cache,
                    "job_slice_count": job_slice_count,
                    "extra_vars": {"env_vars": env_vars} if env_vars else {},
                }
                
                # Set either profile_path or playbook based on mode
                if playbook_mode and profile_path:
                    template_data["playbook"] = profile_path
                    template_data["profile_path"] = None
                elif profile_path:
                    template_data["profile_path"] = profile_path
                    template_data["playbook"] = None
                else:
                    # Neither mode selected or no path provided
                    template_data["profile_path"] = None
                    template_data["playbook"] = None
                
                if create_job_template(template_data):
                    st.success(f"✅ Template '{name}' created successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to create template. Make sure the API server is running.")

# API Docs Page
elif page == "📚 API Docs":
    st.header("API Documentation")
    
    st.markdown("""
    ### REST API Endpoints
    
    The InSpec Execution Server provides a comprehensive REST API for managing job templates and executions.
    
    #### Base URL
    ```
    http://localhost:8080/api/v1
    ```
    
    #### Interactive Documentation
    
    - **Swagger UI**: [http://localhost:8080/docs](http://localhost:8080/docs)
    - **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc)
    
    #### Key Endpoints
    
    **Job Templates**
    - `GET /api/v1/job_templates/` - List all job templates
    - `POST /api/v1/job_templates/` - Create a new job template
    - `GET /api/v1/job_templates/{id}/` - Get a specific template
    - `PUT /api/v1/job_templates/{id}/` - Update a template
    - `DELETE /api/v1/job_templates/{id}/` - Delete a template
    - `POST /api/v1/job_templates/{id}/launch/` - Launch a job
    
    **Jobs**
    - `GET /api/v1/jobs/` - List all jobs
    - `GET /api/v1/jobs/{id}/` - Get a specific job
    - `POST /api/v1/jobs/{id}/cancel/` - Cancel a running job
    - `GET /api/v1/jobs/{id}/stdout/` - Get job output
    
    **Statistics**
    - `GET /api/v1/statistics/` - Get server statistics
    
    ### Job Template Schema
    
    The server supports comprehensive job template schema for both InSpec and Ansible:
    
    **Core Fields:**
    - `name` - Template name (required)
    - `description` - Description text
    - `job_type` - Type: "run", "check", or "scan"
    
    **Execution Sources:**
    - `profile_path` - InSpec profile path or Supermarket ID
    - `playbook` - Ansible playbook path (alternative to profile_path)
    - `project` - Project identifier
    
    **Inventory & Targeting:**
    - `inventory` - Inventory file path
    - `target` - Target hosts (InSpec mode)
    - `limit` - Limit execution to specific hosts
    
    **Tags & Filters:**
    - `tags` - List of tags to run
    - `skip_tags` - List of tags to skip
    
    **Performance:**
    - `forks` - Parallel execution (default: 5)
    - `timeout` - Job timeout in seconds (0 = no timeout)
    - `verbosity` - Output verbosity level (0-4)
    - `job_slice_count` - Parallel job slicing
    
    **Options:**
    - `diff_mode` - Show differences
    - `allow_simultaneous` - Allow concurrent executions
    - `use_fact_cache` - Use fact caching
    - `credentials` - List of credential IDs
    - `extra_vars` - Extra variables dictionary
    
    #### Example: Create InSpec Job Template
    
    ```python
    import requests
    
    template = {
        "name": "Linux Baseline",
        "description": "DevSec Linux Baseline checks",
        "profile_path": "dev-sec/linux-baseline",
        "supermarket": True,
        "reporter": "cli json",
        "tags": ["security", "baseline"],
        "verbosity": 1
    }
    
    response = requests.post(
        "http://localhost:8080/api/v1/job_templates/",
        json=template
    )
    ```
    
    #### Example: Create Playbook Job Template
    
    ```python
    template = {
        "name": "Web Server Compliance",
        "description": "Check web server configuration",
        "playbook": "playbooks/web_compliance.yml",
        "inventory": "inventories/production.yml",
        "job_type": "check",
        "tags": ["compliance", "web"],
        "forks": 10,
        "diff_mode": True,
        "extra_vars": {
            "check_ssl": True,
            "min_version": "2.4"
        }
    }
    
    response = requests.post(
        "http://localhost:8080/api/v1/job_templates/",
        json=template
    )
    ```
    
    #### Example: Launch a Job
    
    ```python
    template_id = "..."  # Your template ID
    
    response = requests.post(
        f"http://localhost:8080/api/v1/job_templates/{template_id}/launch/",
        json={
            "extra_vars": {"override_var": "value"},
            "limit": "web_servers",
            "tags": ["quick_check"],
            "verbosity": 2
        }
    )
    
    job = response.json()
    print(f"Job {job['id']} launched with status: {job['status']}")
    ```
    """)

# Auto-refresh
if auto_refresh and page in ["📊 Dashboard", "📋 Jobs"]:
    time.sleep(5)
    st.rerun()

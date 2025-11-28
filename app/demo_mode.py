# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC) - Demo Mode                                       #
# https://ddc.bot                                                              #
# ============================================================================ #
"""
Demo Mode restrictions for public demo server.
When DDC_MODE=demo is set, certain features are disabled to prevent abuse.
"""

import os
from functools import wraps
from flask import jsonify, request

# Demo Mode Configuration
DEMO_MODE_ENABLED = os.environ.get('DDC_MODE') == 'demo'

# Protected containers that cannot be controlled in demo mode
PROTECTED_CONTAINERS = ['ddc', 'caddy']

# Fixed monitored channel for AAS in demo mode
DEMO_AAS_MONITORED_CHANNEL = '1443591386292289678'

# Demo notice message
DEMO_NOTICE_EN = "This feature is disabled on the demo server"
DEMO_NOTICE_DE = "Diese Funktion ist auf dem Demo-Server deaktiviert"


def is_demo_mode():
    """Check if demo mode is enabled."""
    return DEMO_MODE_ENABLED


def is_protected_container(container_name):
    """Check if a container is protected in demo mode."""
    if not is_demo_mode():
        return False
    return container_name in PROTECTED_CONTAINERS


def get_demo_notice(lang='en'):
    """Get the demo notice message in the specified language."""
    if lang == 'de':
        return DEMO_NOTICE_DE
    return DEMO_NOTICE_EN


def demo_restrict(feature_name='this feature'):
    """
    Decorator to restrict API endpoints in demo mode.
    Returns 403 with demo notice if demo mode is enabled.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if is_demo_mode():
                return jsonify({
                    'success': False,
                    'error': f'{DEMO_NOTICE_EN}',
                    'demo_mode': True,
                    'restricted_feature': feature_name
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def demo_restrict_container(f):
    """
    Decorator to restrict container actions for protected containers.
    Checks container_name in URL parameters or request data.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_demo_mode():
            return f(*args, **kwargs)

        # Check URL parameters
        container_name = kwargs.get('container_name') or kwargs.get('name')

        # Check request data
        if not container_name:
            if request.is_json:
                data = request.get_json(silent=True) or {}
                container_name = data.get('container_name') or data.get('container')
            elif request.form:
                container_name = request.form.get('container_name') or request.form.get('container')

        if container_name and is_protected_container(container_name):
            return jsonify({
                'success': False,
                'error': f'Container "{container_name}" is protected on the demo server',
                'demo_mode': True,
                'protected_container': container_name
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def get_demo_context():
    """
    Get demo mode context for templates.
    Returns a dict with demo mode settings.
    """
    return {
        'is_demo_mode': is_demo_mode(),
        'demo_notice': get_demo_notice(),
        'protected_containers': PROTECTED_CONTAINERS if is_demo_mode() else [],
        'demo_aas_channel': DEMO_AAS_MONITORED_CHANNEL if is_demo_mode() else None
    }


def filter_containers_for_demo(containers):
    """
    Filter container list for demo mode.
    Returns containers with protected flag added.
    """
    if not is_demo_mode():
        return containers

    result = []
    for container in containers:
        container_copy = dict(container) if isinstance(container, dict) else container
        name = container_copy.get('name') or container_copy.get('container_name', '')
        if isinstance(container_copy, dict):
            container_copy['demo_protected'] = name in PROTECTED_CONTAINERS
        result.append(container_copy)
    return result


def get_allowed_task_containers(all_containers):
    """
    Get list of containers that can be targeted by tasks in demo mode.
    Excludes protected containers.
    """
    if not is_demo_mode():
        return all_containers

    return [c for c in all_containers
            if (c.get('name') or c.get('container_name', '')) not in PROTECTED_CONTAINERS]

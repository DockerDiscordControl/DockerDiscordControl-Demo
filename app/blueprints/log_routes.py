# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC)                                                  #
# https://ddc.bot                                                              #
# Copyright (c) 2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #
import os
from flask import Blueprint, Response, current_app, request, jsonify
from app.auth import auth

log_bp = Blueprint('log_bp', __name__)


@log_bp.route('/test')
@auth.login_required
def test_logs_route():
    """Simple test endpoint to verify log routes are working."""
    return Response("Log routes are working! Test successful.", mimetype='text/plain')


def _simple_read_logs(max_lines=500):
    """Simple fallback log reader - tries multiple log files."""
    log_paths = [
        '/app/logs/supervisord.log',
        '/var/log/supervisor/supervisord.log',
        '/app/logs/bot.log',
        '/app/logs/discord.log',
    ]
    for path in log_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    return ''.join(lines[-max_lines:])
        except Exception:
            continue
    return None


def _simple_docker_logs(container_name, max_lines=500):
    """Simple Docker log reader without async complexity."""
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get(container_name)
        logs = container.logs(tail=max_lines, stdout=True, stderr=True)
        return logs.decode('utf-8', errors='replace')
    except Exception as e:
        current_app.logger.warning(f"Simple Docker logs failed: {e}")
        return None


@log_bp.route('/container_logs/<container_name>')
@auth.login_required
def get_container_logs(container_name):
    """Get container logs using ContainerLogService."""
    try:
        # Use ContainerLogService for business logic
        from services.web.container_log_service import get_container_log_service, ContainerLogRequest

        service = get_container_log_service()
        request_obj = ContainerLogRequest(
            container_name=container_name,
            max_lines=500
        )

        # Get logs through service
        result = service.get_container_logs(request_obj)

        if result.success:
            return Response(result.content, mimetype='text/plain')
        else:
            # Log detailed error but return generic message to user
            current_app.logger.warning(f"Container log request failed: {result.error}")
            # Try simple fallback
            logs = _simple_docker_logs(container_name) or _simple_read_logs()
            if logs:
                return Response(f"[Fallback mode]\n{logs}", mimetype='text/plain')
            return Response(f"Failed to fetch container logs: {result.error}", status=result.status_code, mimetype='text/plain')

    except (ImportError, AttributeError, RuntimeError) as e:
        # Service dependency errors - try simple fallback
        current_app.logger.error(f"Service error in get_container_logs route: {e}", exc_info=True)
        logs = _simple_docker_logs(container_name) or _simple_read_logs()
        if logs:
            return Response(f"[Fallback mode - service error]\n{logs}", mimetype='text/plain')
        return Response(f"Service error: {str(e)}", status=500, mimetype='text/plain')
    except (ValueError, TypeError, KeyError) as e:
        # Data errors - try simple fallback
        current_app.logger.error(f"Data error in get_container_logs route: {e}", exc_info=True)
        logs = _simple_docker_logs(container_name) or _simple_read_logs()
        if logs:
            return Response(f"[Fallback mode - data error]\n{logs}", mimetype='text/plain')
        return Response(f"Data error: {str(e)}", status=500, mimetype='text/plain')

@log_bp.route('/bot_logs')
@auth.login_required
def get_bot_logs():
    """Get bot logs using ContainerLogService."""
    try:
        from services.web.container_log_service import get_container_log_service, FilteredLogRequest, LogType
        service = get_container_log_service()
        request_obj = FilteredLogRequest(log_type=LogType.BOT, max_lines=500)
        result = service.get_filtered_logs(request_obj)
        if result.success:
            return Response(result.content, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"Bot logs error: {e}", exc_info=True)

    # Fallback: try to read bot.log directly
    logs = _simple_read_logs() or "No bot logs available"
    return Response(logs, mimetype='text/plain')

@log_bp.route('/discord_logs')
@auth.login_required
def get_discord_logs():
    """Get Discord logs using ContainerLogService."""
    try:
        from services.web.container_log_service import get_container_log_service, FilteredLogRequest, LogType
        service = get_container_log_service()
        request_obj = FilteredLogRequest(log_type=LogType.DISCORD, max_lines=500)
        result = service.get_filtered_logs(request_obj)
        if result.success:
            return Response(result.content, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"Discord logs error: {e}", exc_info=True)

    logs = _simple_read_logs() or "No Discord logs available"
    return Response(logs, mimetype='text/plain')

@log_bp.route('/webui_logs')
@auth.login_required
def get_webui_logs():
    """Get Web UI logs using ContainerLogService."""
    try:
        from services.web.container_log_service import get_container_log_service, FilteredLogRequest, LogType
        service = get_container_log_service()
        request_obj = FilteredLogRequest(log_type=LogType.WEBUI, max_lines=500)
        result = service.get_filtered_logs(request_obj)
        if result.success:
            return Response(result.content, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"WebUI logs error: {e}", exc_info=True)

    logs = _simple_read_logs() or "No Web UI logs available"
    return Response(logs, mimetype='text/plain')

@log_bp.route('/application_logs')
@auth.login_required
def get_application_logs():
    """Get application logs using ContainerLogService."""
    try:
        from services.web.container_log_service import get_container_log_service, FilteredLogRequest, LogType
        service = get_container_log_service()
        request_obj = FilteredLogRequest(log_type=LogType.APPLICATION, max_lines=500)
        result = service.get_filtered_logs(request_obj)
        if result.success:
            return Response(result.content, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"Application logs error: {e}", exc_info=True)

    logs = _simple_read_logs() or "No application logs available"
    return Response(logs, mimetype='text/plain')

@log_bp.route('/action_logs')
@auth.login_required
def get_action_logs():
    """Get action logs using ContainerLogService."""
    try:
        from services.web.container_log_service import get_container_log_service, ActionLogRequest
        service = get_container_log_service()
        request_obj = ActionLogRequest(format_type="text", limit=500)
        result = service.get_action_logs(request_obj)
        if result.success:
            return Response(result.content, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"Action logs error: {e}", exc_info=True)

    return Response("No action logs available", mimetype='text/plain')

@log_bp.route('/action_logs_json')
@auth.login_required
def get_action_logs_json():
    """Get action logs as JSON using ContainerLogService."""
    try:
        # Use ContainerLogService for business logic
        from services.web.container_log_service import get_container_log_service, ActionLogRequest

        service = get_container_log_service()
        request_obj = ActionLogRequest(
            format_type="json",
            limit=500
        )

        # Get logs through service
        result = service.get_action_logs(request_obj)

        if result.success:
            return jsonify(result.data)
        else:
            # Log detailed error but return generic message to user
            current_app.logger.error(f"Action log JSON request failed: {result.error}")
            return jsonify({'success': False, 'error': 'Failed to fetch action logs'}), result.status_code

    except (ImportError, AttributeError, RuntimeError) as e:
        # Service dependency errors (container_log_service unavailable, service method failures)
        current_app.logger.error(f"Service error in get_action_logs_json route: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Service error occurred'}), 500
    except (ValueError, TypeError, KeyError) as e:
        # Data errors (invalid request parameters, response processing failures, JSON serialization)
        current_app.logger.error(f"Data error in get_action_logs_json route: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Data error occurred'}), 500

@log_bp.route('/clear_logs', methods=['POST'])
@auth.login_required
def clear_logs():
    """Clear logs using ContainerLogService."""
    try:
        # Use ContainerLogService for business logic
        from services.web.container_log_service import get_container_log_service, ClearLogRequest

        log_type = request.json.get('log_type', 'container') if request.json else 'container'

        service = get_container_log_service()
        request_obj = ClearLogRequest(log_type=log_type)

        # Clear logs through service
        result = service.clear_logs(request_obj)

        if result.success:
            return jsonify(result.data)
        else:
            # Log detailed error but return generic message to user
            current_app.logger.error(f"Clear logs request failed: {result.error}")
            return jsonify({'success': False, 'message': 'Failed to clear logs'}), result.status_code

    except (ImportError, AttributeError, RuntimeError) as e:
        # Service dependency errors (container_log_service unavailable, service method failures)
        current_app.logger.error(f"Service error in clear_logs route: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Service error occurred'}), 500
    except (ValueError, TypeError, KeyError) as e:
        # Data errors (invalid request parameters, response processing failures, JSON parsing)
        current_app.logger.error(f"Data error in clear_logs route: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Data error occurred'}), 500

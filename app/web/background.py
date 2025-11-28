# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC)                                                  #
# https://ddc.bot                                                              #
# Copyright (c) 2025 MAX                                                  #
# Licensed under the MIT License                                               #
# ============================================================================ #
"""Background service orchestration for the web app."""

from __future__ import annotations

import os

from flask import Flask

from app.utils.shared_data import load_active_containers_from_config
from app.utils.web_helpers import (
    start_background_refresh,
    start_mech_decay_background,
    stop_background_refresh,
    stop_mech_decay_background,
)

from .compat import HAS_GEVENT, apply_gevent_fork_workaround, spawn_delayed

# Demo Reset Service reference
_demo_reset_service = None


def _is_enabled(var_name: str) -> bool:
    return os.environ.get(var_name, "true").lower() != "false"


def register_background_services(app: Flask) -> None:
    """Start background helpers and register teardown hooks."""
    apply_gevent_fork_workaround(app.logger)

    with app.app_context():
        app.logger.info("Starting Docker cache background refresh thread")

        if _is_enabled("DDC_ENABLE_BACKGROUND_REFRESH"):
            if HAS_GEVENT:
                spawn_delayed(2.0, start_background_refresh, app.logger)
            else:
                start_background_refresh(app.logger)
        else:
            app.logger.info("Background Docker cache refresh disabled by environment setting")

        app.logger.info("Loading active containers from config")
        active_containers = load_active_containers_from_config()
        app.logger.info("Loaded %d active containers: %s", len(active_containers), active_containers)

        if _is_enabled("DDC_ENABLE_MECH_DECAY"):
            if HAS_GEVENT:
                spawn_delayed(2.0, start_mech_decay_background, app.logger)
            else:
                start_mech_decay_background(app.logger)
        else:
            app.logger.info("Mech decay background task disabled by environment setting")

        # Start Demo Reset Service (only in demo mode)
        global _demo_reset_service
        if os.environ.get('DDC_MODE') == 'demo':
            try:
                from services.demo.demo_reset_service import get_demo_reset_service
                _demo_reset_service = get_demo_reset_service()
                if HAS_GEVENT:
                    spawn_delayed(5.0, _demo_reset_service.start)
                else:
                    _demo_reset_service.start()
                app.logger.info("Demo Reset Service started - configs will reset every hour at :00")
            except Exception as e:
                app.logger.error(f"Failed to start Demo Reset Service: {e}", exc_info=True)

        @app.teardown_appcontext
        def cleanup_background_threads(exception=None):  # type: ignore[override]
            try:
                app.logger.debug("Stopping background threads on app teardown")

                from app.utils.web_helpers import background_refresh_thread, mech_decay_thread

                if background_refresh_thread is not None:
                    stop_background_refresh(app.logger)

                if mech_decay_thread is not None:
                    stop_mech_decay_background(app.logger)

                # Stop Demo Reset Service
                if _demo_reset_service is not None:
                    _demo_reset_service.stop()
                    app.logger.debug("Demo Reset Service stopped")
            except (IOError, OSError, PermissionError, RuntimeError) as e:
                app.logger.error("Error during background thread cleanup: %s", e, exc_info=True)

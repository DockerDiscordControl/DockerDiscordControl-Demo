# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC) - Demo Reset Service                              #
# https://ddc.bot                                                              #
# Copyright (c) 2025 MAX                                                       #
# Licensed under the MIT License                                               #
# ============================================================================ #

"""
Demo Reset Service - Resets demo server configuration hourly

This service:
1. Saves the current configuration as "demo defaults" on first run
2. Restores these defaults every hour at :00
3. Only active when DDC_MODE=demo
"""

import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger('ddc.demo_reset_service')

# Demo reset constants
DEMO_DEFAULTS_DIR = "demo_defaults"
CONFIG_DIRS_TO_BACKUP = ["containers", "channels"]
CONFIG_FILES_TO_BACKUP = ["config.json", "tasks.json"]
RESET_HOUR_MINUTE = 0  # Reset at :00 of every hour


def is_demo_mode() -> bool:
    """Check if running in demo mode."""
    return os.environ.get('DDC_MODE') == 'demo'


class DemoResetService:
    """Service for managing hourly demo configuration resets."""

    def __init__(self):
        """Initialize the Demo Reset Service."""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.base_dir = Path(__file__).parents[2]  # Go up to project root
        self.config_dir = self.base_dir / "config"
        self.defaults_dir = self.config_dir / DEMO_DEFAULTS_DIR
        self.last_reset_hour = -1

    def start(self) -> bool:
        """Start the Demo Reset Service."""
        if not is_demo_mode():
            logger.info("Demo Reset Service not started - not in demo mode")
            return False

        if self.running:
            logger.warning("Demo Reset Service is already running")
            return False

        # Ensure defaults are saved on first start
        self._ensure_defaults_exist()

        self.running = True
        self.thread = threading.Thread(target=self._run_service, daemon=True)
        self.thread.start()
        logger.info("Demo Reset Service started - will reset config every hour at :00")
        return True

    def stop(self) -> bool:
        """Stop the Demo Reset Service."""
        if not self.running:
            return False

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Demo Reset Service stopped")
        return True

    def _run_service(self):
        """Main service loop - checks every minute if reset is needed."""
        logger.info("Demo Reset Service loop started")

        while self.running:
            try:
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute

                # Reset at the top of every hour (minute 0)
                if current_minute == RESET_HOUR_MINUTE and current_hour != self.last_reset_hour:
                    logger.info(f"Hourly reset triggered at {now.strftime('%H:%M')}")
                    self._reset_to_defaults()
                    self.last_reset_hour = current_hour

                # Sleep for 30 seconds before next check
                time.sleep(30)

            except Exception as e:
                logger.error(f"Error in Demo Reset Service loop: {e}", exc_info=True)
                time.sleep(60)  # Wait longer on error

    def _ensure_defaults_exist(self):
        """Ensure demo defaults are saved. Creates them if they don't exist."""
        if not self.defaults_dir.exists():
            logger.info("Creating demo defaults for the first time")
            self._save_current_as_defaults()
        else:
            logger.info(f"Demo defaults already exist at {self.defaults_dir}")

    def _save_current_as_defaults(self):
        """Save current configuration as demo defaults."""
        try:
            # Create defaults directory
            self.defaults_dir.mkdir(parents=True, exist_ok=True)

            # Backup config files
            for filename in CONFIG_FILES_TO_BACKUP:
                src = self.config_dir / filename
                dst = self.defaults_dir / filename
                if src.exists():
                    shutil.copy2(src, dst)
                    logger.info(f"Saved default: {filename}")

            # Backup config directories
            for dirname in CONFIG_DIRS_TO_BACKUP:
                src_dir = self.config_dir / dirname
                dst_dir = self.defaults_dir / dirname
                if src_dir.exists():
                    if dst_dir.exists():
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                    logger.info(f"Saved default directory: {dirname}")

            # Create a timestamp file
            timestamp_file = self.defaults_dir / ".defaults_created"
            timestamp_file.write_text(datetime.now().isoformat())

            logger.info("Demo defaults saved successfully")

        except Exception as e:
            logger.error(f"Failed to save demo defaults: {e}", exc_info=True)

    def _reset_to_defaults(self):
        """Reset configuration to demo defaults."""
        try:
            if not self.defaults_dir.exists():
                logger.warning("No demo defaults found - cannot reset")
                return

            reset_count = 0

            # Restore config files
            for filename in CONFIG_FILES_TO_BACKUP:
                src = self.defaults_dir / filename
                dst = self.config_dir / filename
                if src.exists():
                    shutil.copy2(src, dst)
                    reset_count += 1
                    logger.debug(f"Restored: {filename}")

            # Restore config directories
            for dirname in CONFIG_DIRS_TO_BACKUP:
                src_dir = self.defaults_dir / dirname
                dst_dir = self.config_dir / dirname
                if src_dir.exists():
                    if dst_dir.exists():
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                    reset_count += 1
                    logger.debug(f"Restored directory: {dirname}")

            # Touch the config update timestamp for cache invalidation
            self._touch_config_timestamp()

            logger.info(f"Demo reset complete - restored {reset_count} items")

        except Exception as e:
            logger.error(f"Failed to reset to demo defaults: {e}", exc_info=True)

    def _touch_config_timestamp(self):
        """Touch the config timestamp file for cross-process cache invalidation."""
        try:
            timestamp_file = self.config_dir / '.config_updated'
            timestamp_file.touch()
            logger.debug("Touched config timestamp for cache invalidation")
        except Exception as e:
            logger.warning(f"Failed to touch config timestamp: {e}")

    def force_reset(self) -> bool:
        """Force an immediate reset to defaults (for manual triggering)."""
        if not is_demo_mode():
            logger.warning("Force reset rejected - not in demo mode")
            return False

        logger.info("Force reset triggered")
        self._reset_to_defaults()
        return True

    def save_current_as_new_defaults(self) -> bool:
        """Save current configuration as new demo defaults."""
        if not is_demo_mode():
            logger.warning("Save defaults rejected - not in demo mode")
            return False

        logger.info("Saving current config as new demo defaults")
        self._save_current_as_defaults()
        return True


# Singleton instance
_service_instance: Optional[DemoResetService] = None


def get_demo_reset_service() -> DemoResetService:
    """Get the singleton Demo Reset Service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DemoResetService()
    return _service_instance


def start_demo_reset_service() -> bool:
    """Start the Demo Reset Service (convenience function)."""
    return get_demo_reset_service().start()


def stop_demo_reset_service() -> bool:
    """Stop the Demo Reset Service (convenience function)."""
    return get_demo_reset_service().stop()

# -*- coding: utf-8 -*-
# ============================================================================ #
# DockerDiscordControl (DDC) - Demo Update Messages Service                    #
# https://ddc.bot                                                              #
# Copyright (c) 2025 MAX                                                       #
# Licensed under the MIT License                                               #
# ============================================================================ #

"""
Demo Update Messages Service - Sends realistic-looking update messages to the update channel

This service:
1. Sends 12 different demo update messages throughout each hour
2. Messages are sent at random intervals (max 10 minutes between messages)
3. Each message includes a disclaimer that it's a demo message
4. Only active when DDC_MODE=demo
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger('ddc.demo_update_messages')

# Demo mode check
DEMO_MODE = os.environ.get('DDC_MODE') == 'demo'

# Update channel ID for demo
UPDATE_CHANNEL_ID = 1443591386292289678

# Disclaimer text
DISCLAIMER = "\n\n-# ⚠️ *This is a DEMO message for testing purposes only. It does not reflect real events or actual software updates.*"

# 12 Demo update messages for different containers (max 5 lines each)
DEMO_UPDATE_MESSAGES = [
    {
        "container": "minecraft",
        "title": "Minecraft #updates",
        "content": """🎮 **Server Update v1.21.4**
Performance optimizations & plugin updates installed.
Status: ✅ Online"""
    },
    {
        "container": "valheim",
        "title": "Valheim #patch-notes",
        "content": """⚔️ **Patch 0.218.15 - Ashlands Hotfix**
Fixed spawn rates, improved stability, reduced memory usage.
World backup created automatically."""
    },
    {
        "container": "plex",
        "title": "Plex #updates",
        "content": """📺 **Plex Media Server v1.41.2**
HDR tone mapping improved, audio sync fixed.
Library scan running in background."""
    },
    {
        "container": "jellyfin",
        "title": "Jellyfin #updates",
        "content": """🎬 **Jellyfin v10.9.11**
Playback fixes, improved library scanning, FFmpeg updated.
All plugins compatible. ✅"""
    },
    {
        "container": "grafana",
        "title": "Grafana #monitoring",
        "content": """📊 **Grafana v11.3.1 Deployed**
New visualizations, better Prometheus performance.
All dashboards preserved."""
    },
    {
        "container": "gitea",
        "title": "Gitea #updates",
        "content": """🐙 **Gitea v1.22.4**
Security patches applied, webhook fixes, better LFS support.
All repositories intact."""
    },
    {
        "container": "uptime-kuma",
        "title": "Uptime Kuma #status",
        "content": """📡 **Uptime Kuma v1.23.15**
New notification providers, improved ping accuracy.
24 monitors active, 99.98% uptime."""
    },
    {
        "container": "satisfactory",
        "title": "Satisfactory #updates",
        "content": """🏭 **Update 8.1 Installed**
New buildables, better multiplayer sync, reduced CPU usage.
Save file backed up. Factory must grow!"""
    },
    {
        "container": "minecraft",
        "title": "Minecraft #maintenance",
        "content": """🔧 **Weekly Maintenance Complete**
World backup: 2.3 GB, chunks pruned, TPS: 20.
Ready to play! 🎮"""
    },
    {
        "container": "valheim",
        "title": "Valheim #events",
        "content": """🎉 **Double Loot Weekend Active!**
2x drops, more treasure chests, faster boss respawns.
Event ends Sunday 23:59 UTC. ⚔️"""
    },
    {
        "container": "plex",
        "title": "Plex #library",
        "content": """📚 **Library Scan Complete**
Movies: 1,247 (+12) | TV: 4,521 episodes | Music: 15,832 tracks
Storage: 8.2 TB / 12 TB 🍿"""
    },
    {
        "container": "jellyfin",
        "title": "Jellyfin #plugins",
        "content": """🔌 **Plugins Updated**
OpenSubtitles, Fanart, TMDb Box Sets, Playback Reporting.
No restart required. ✅"""
    }
]


class DemoUpdateMessagesService:
    """Service for sending demo update messages to the update channel."""

    def __init__(self, bot):
        """Initialize the Demo Update Messages Service."""
        self.bot = bot
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.messages_sent_this_hour = 0
        self.current_hour = -1

    async def start(self) -> bool:
        """Start the Demo Update Messages Service."""
        if not DEMO_MODE:
            logger.info("Demo Update Messages Service not started - not in demo mode")
            return False

        if self.running:
            logger.warning("Demo Update Messages Service is already running")
            return False

        self.running = True
        self.task = asyncio.create_task(self._run_service())
        logger.info("Demo Update Messages Service started - will send 12 messages per hour")
        return True

    async def stop(self) -> bool:
        """Stop the Demo Update Messages Service."""
        if not self.running:
            return False

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Demo Update Messages Service stopped")
        return True

    async def _run_service(self):
        """Main service loop - sends messages throughout each hour."""
        logger.info("Demo Update Messages Service loop started")

        while self.running:
            try:
                now = datetime.now()
                current_hour = now.hour

                # Reset counter at the start of each hour
                if current_hour != self.current_hour:
                    self.current_hour = current_hour
                    self.messages_sent_this_hour = 0
                    logger.info(f"New hour started ({current_hour}:00) - resetting message counter")

                # Check if we still have messages to send this hour
                if self.messages_sent_this_hour < 12:
                    # Calculate remaining time in this hour
                    minutes_remaining = 60 - now.minute
                    messages_remaining = 12 - self.messages_sent_this_hour

                    if messages_remaining > 0 and minutes_remaining > 0:
                        # Calculate average interval, but cap at 10 minutes max
                        avg_interval = min(10, minutes_remaining / messages_remaining)

                        # Add some randomness (50% to 150% of average)
                        wait_minutes = avg_interval * random.uniform(0.5, 1.5)
                        wait_minutes = min(wait_minutes, 10)  # Cap at 10 minutes
                        wait_minutes = max(wait_minutes, 0.5)  # Minimum 30 seconds

                        wait_seconds = wait_minutes * 60

                        logger.debug(f"Waiting {wait_minutes:.1f} minutes before next message")
                        await asyncio.sleep(wait_seconds)

                        # Send a random message
                        if self.running:
                            await self._send_random_message()
                    else:
                        # Wait until next hour
                        await asyncio.sleep(60)
                else:
                    # All messages sent this hour, wait for next hour
                    await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("Demo Update Messages Service cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Demo Update Messages Service loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _send_random_message(self):
        """Send a random demo update message to the update channel."""
        try:
            channel = self.bot.get_channel(UPDATE_CHANNEL_ID)
            if not channel:
                logger.warning(f"Update channel {UPDATE_CHANNEL_ID} not found")
                return

            # Pick a random message
            message_data = random.choice(DEMO_UPDATE_MESSAGES)

            # Format the message
            now = datetime.now()
            timestamp = now.strftime("%d.%m.%y, %H:%M")

            full_message = f"**{message_data['title']}**\n"
            full_message += f"— {timestamp}\n\n"
            full_message += message_data['content']
            full_message += DISCLAIMER

            # Send the message
            await channel.send(full_message)

            self.messages_sent_this_hour += 1
            logger.info(f"Sent demo update message #{self.messages_sent_this_hour}/12: {message_data['container']}")

        except Exception as e:
            logger.error(f"Failed to send demo update message: {e}", exc_info=True)

    async def send_test_message(self) -> bool:
        """Send a single test message (for manual testing)."""
        if not DEMO_MODE:
            logger.warning("Test message rejected - not in demo mode")
            return False

        await self._send_random_message()
        return True


# Singleton instance
_service_instance: Optional[DemoUpdateMessagesService] = None


def get_demo_update_messages_service(bot=None) -> Optional[DemoUpdateMessagesService]:
    """Get the singleton Demo Update Messages Service instance."""
    global _service_instance
    if _service_instance is None and bot is not None:
        _service_instance = DemoUpdateMessagesService(bot)
    return _service_instance


async def start_demo_update_messages_service(bot) -> bool:
    """Start the Demo Update Messages Service (convenience function)."""
    service = get_demo_update_messages_service(bot)
    if service:
        return await service.start()
    return False


async def stop_demo_update_messages_service() -> bool:
    """Stop the Demo Update Messages Service (convenience function)."""
    service = get_demo_update_messages_service()
    if service:
        return await service.stop()
    return False

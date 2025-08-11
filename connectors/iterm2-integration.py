#!/usr/bin/env python3

import iterm2
import asyncio
import aiohttp
import os
import time

# Configuration
BACKEND_URL = "http://127.0.0.1:37777"
DEVSYSTEM_PATH = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
CHECK_INTERVAL = 2  # seconds

async def main(connection):
    app = await iterm2.async_get_app(connection)
    
    # Monitor for screenshot webhook
    async def check_for_screenshots():
        last_screenshot = None
        
        while True:
            try:
                # Check for new screenshot signal
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{BACKEND_URL}/webhook/status") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('new_screenshot') and data.get('filename') != last_screenshot:
                                last_screenshot = data['filename']
                                screenshot_path = f"{DEVSYSTEM_PATH}/connectors/ScreenShots/{last_screenshot}"
                                
                                # Find the right terminal window
                                for window in app.windows:
                                    for tab in window.tabs:
                                        for session in tab.sessions:
                                            # Get current directory
                                            pwd = await session.async_get_variable("path")
                                            
                                            # Check if this session is in DevSystem
                                            if pwd and DEVSYSTEM_PATH in pwd:
                                                # Check if it's a Claude terminal
                                                hostname = await session.async_get_variable("hostname")
                                                command = await session.async_get_variable("commandLine")
                                                
                                                if command and "claude" in command.lower():
                                                    # Send the screenshot path to this terminal
                                                    await session.async_send_text(f"\n# Screenshot saved: {screenshot_path}\n")
                                                    await session.async_send_text(f"# Auto-inserting into Claude context...\n")
                                                    
                                                    # Insert screenshot viewing command
                                                    await session.async_send_text(f"open {screenshot_path}\n")
                                                    
                                                    # Mark this session
                                                    await session.async_set_name(f"📸 Claude - DevSystem")
                                                    
                                                    # Clear the webhook
                                                    async with session.post(f"{BACKEND_URL}/webhook/clear"):
                                                        pass
                                                    
                                                    break
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(CHECK_INTERVAL)
    
    # Mark DevSystem terminals
    async def mark_devsystem_terminals():
        while True:
            for window in app.windows:
                for tab in window.tabs:
                    for session in tab.sessions:
                        pwd = await session.async_get_variable("path")
                        if pwd and DEVSYSTEM_PATH in pwd:
                            current_name = await session.async_get_name()
                            if not current_name or "DevSystem" not in current_name:
                                command = await session.async_get_variable("commandLine")
                                if command and "claude" in command.lower():
                                    await session.async_set_name("🤖 Claude - DevSystem")
                                else:
                                    await session.async_set_name("💻 DevSystem")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    # Run both tasks
    await asyncio.gather(
        check_for_screenshots(),
        mark_devsystem_terminals()
    )

# iTerm2 connection
iterm2.run_forever(main)
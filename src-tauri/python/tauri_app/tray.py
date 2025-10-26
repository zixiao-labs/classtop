"""
System tray functionality for ClassTop application.
"""

import os
from typing import Optional

from pytauri.tray import TrayIcon, TrayIconEvent, MouseButton, MouseButtonState
from pytauri.menu import Menu, MenuItem, PredefinedMenuItem
from pytauri.image import Image
from pytauri import AppHandle, Manager, WebviewUrl
from pytauri.webview import WebviewWindowBuilder
from . import logger


class SystemTray:
    """Handles system tray icon and menu functionality."""

    def __init__(self):
        self.tray: Optional[TrayIcon] = None
        self.portal = None
        self.app_handle: Optional[AppHandle] = None

    def toggle_window(self, window_name: str) -> bool:
        """Toggle window visibility using PyTauri API"""
        try:
            # Get the window by name
            window = Manager.get_webview_window(self.app_handle, window_name)

            if not window:
                logger.log_message("warning", f"Window '{window_name}' not found.")

                # Create window based on configuration
                if window_name == "main":
                    logger.log_message("info", f"Creating window '{window_name}'")
                    # Create main window with configuration optimized for small screens
                    window = WebviewWindowBuilder.build(
                        self.app_handle,
                        window_name,
                        WebviewUrl.App("/"),  # Use WebviewUrl.App for internal routes
                        title="ClassTop",
                        inner_size=(1000.0, 700.0),  # Reduced from 1200x800 for better compatibility
                        min_inner_size=(800.0, 600.0),
                        prevent_overflow=True,  # Prevent window from overflowing screen bounds
                        resizable=True,
                        maximizable=True,
                        minimizable=True,
                        closable=True,
                        decorations=True,
                        always_on_top=False,
                        skip_taskbar=False,
                        transparent=False,
                        shadow=True,
                        center=True,  # Center the window instead of fixed position
                        focused=True,
                        visible=True
                    )
                    logger.log_message("info", f"Created window '{window_name}'")
                    return True
                else:
                    logger.log_message("error", f"Unknown window '{window_name}'")
                    return False

            # Check if window is visible and toggle
            is_visible = window.is_visible()

            if is_visible:
                window.hide()
            else:
                window.show()
                # Try to focus the window after showing
                try:
                    window.set_focus()
                except:
                    pass  # Focus might fail on some systems

            return not is_visible
        except Exception as e:
            logger.log_message("error", f"Error toggling window: {e}")
            return False

    def handle_tray_event(self, tray: TrayIcon, event: TrayIconEvent):
        """Handle system tray icon events"""
        if isinstance(event, TrayIconEvent.Click):
            # Left click - toggle main window
            # Only respond to button release to avoid double-triggering
            if event.button == MouseButton.Left and event.button_state == MouseButtonState.Up:
                self.toggle_window("main")

    def handle_menu_event(self, app, event):
        """Handle menu item clicks"""
        try:
            # event is the menu item id as a string
            if event == "show_topbar":
                # Toggle topbar window
                self.toggle_window("topbar")

            elif event == "quit":
                # Quit the application
                if self.app_handle:
                    self.app_handle.exit(0)

        except Exception as e:
            logger.log_message("error", f"Error handling menu event: {e}")

    def create_tray_menu(self) -> Menu:
        """Create the system tray context menu"""
        # Create menu with items using the correct API
        menu_items = [
            MenuItem.with_id(self.app_handle, "show_topbar", "Show/Hide Topbar", True),
            PredefinedMenuItem.separator(self.app_handle),
            MenuItem.with_id(self.app_handle, "quit", "Quit", True)
        ]

        menu = Menu.with_items(self.app_handle, menu_items)
        return menu

    def setup_tray(self, app_handle, portal) -> bool:
        """
        Setup system tray icon and menu.

        Args:
            app_handle: The Tauri app handle
            portal: The asyncio portal for async operations

        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Store references for event handlers (must be before create_tray_menu)
            self.portal = portal
            self.app_handle = app_handle

            # Create tray icon using app handle
            self.tray = TrayIcon(app_handle)

            # Set tray icon (using 32x32.png for system tray)
            # Use Tauri's resource path to handle both dev and production environments
            try:
                path_resolver = Manager.path(app_handle)
                resource_dir = path_resolver.resource_dir()
                icon_path = resource_dir / "icons" / "32x32.png"

                # Log the path for debugging
                logger.log_message("info", f"Trying resource path: {icon_path}")

                if not icon_path.exists():
                    # Fallback to relative path for dev environment
                    icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "32x32.png")
                    logger.log_message("info", f"Resource path not found, trying relative path: {icon_path}")

                # Load icon as Image object
                with open(icon_path, 'rb') as f:
                    icon_data = f.read()
                icon_image = Image.from_bytes(icon_data)
                self.tray.set_icon(icon_image)
            except Exception as e:
                logger.log_message("error", f"Failed to load icon: {e}")
                raise

            # Set tooltip
            self.tray.set_tooltip("ClassTop - System Tray")

            # Create and set menu (after app_handle is set)
            menu = self.create_tray_menu()
            self.tray.set_menu(menu)
            self.tray.set_show_menu_on_left_click(False)  # 左键不弹菜单

            # Set event handlers
            self.tray.on_tray_icon_event(self.handle_tray_event)
            self.tray.on_menu_event(self.handle_menu_event)

            # Make tray visible
            self.tray.set_visible(True)

            return True

        except Exception as e:
            logger.log_message("error", f"Error setting up system tray: {e}")
            return False
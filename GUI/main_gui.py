# main_gui.py - Main application entry point using MVC architecture

from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
from PyQt6.QtWidgets import QApplication
import sys

# Import MVC components
from controllers import MainController


def qt_message_handler(mode, context, message):
    """Filter Qt messages to suppress unnecessary warnings"""
    # Suppress specific setGeometry messages from Windows
    if "QWindowsWindow::setGeometry" in message:
        return
    if "Unable to set geometry" in message:
        return
    if "MINMAXINFO" in message:
        return
    
    # Allow other important messages
    if mode == QtMsgType.QtCriticalMsg or mode == QtMsgType.QtFatalMsg:
        print(f"Qt {mode}: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        # Only show warnings that are not about geometry
        if not any(keyword in message for keyword in ["setGeometry", "geometry", "MINMAXINFO"]):
            print(f"Qt Warning: {message}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Install Qt message filter to suppress unnecessary warnings
    qInstallMessageHandler(qt_message_handler)
    
    # Create main controller (handles all MVC coordination)
    main_controller = MainController()
    
    # Get and show main window
    main_window = main_controller.get_main_window()
    main_window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


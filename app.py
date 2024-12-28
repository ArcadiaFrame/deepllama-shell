import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QProcess, pyqtSlot, QObject
from PyQt5.QtWebChannel import QWebChannel
import os
from PyQt5.QtGui import QIcon

class TerminalBridge(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_terminal()
    
    def start_terminal(self):
        # Initialize terminal process
        self.process = QProcess()
        self.process.setProgram("cmd.exe")
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.start()
        
    @pyqtSlot(str)
    def send_command(self, command):
        self.process.write((command + '\n').encode())
        
    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode()
        # Send output to JavaScript
        self.page.runJavaScript(f'addTerminalOutput(`{data.strip()}`)')
        
    def handle_error(self):
        data = self.process.readAllStandardError().data().decode()
        self.page.runJavaScript(f'addTerminalOutput(`{data.strip()}`)')
        
    @pyqtSlot()
    def reset_terminal(self):
        # Kill the current process
        if self.process:
            self.process.kill()
            self.process.waitForFinished()
            
        # Clear the terminal output in JavaScript
        self.page.runJavaScript('terminalOutput.innerHTML = ""')
        
        # Start a new terminal process
        self.start_terminal()
        
        # Add welcome message
        self.page.runJavaScript('addTerminalOutput("Terminal has been reset. Welcome to the new session!")')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deep Shell 🐚")
        self.showMaximized()
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
        self.setWindowIcon(QIcon(icon_path))
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create web view widget
        self.web_view = QWebEngineView()
        
        # Set up web channel for JavaScript communication
        self.channel = QWebChannel()
        self.terminal_bridge = TerminalBridge()
        self.channel.registerObject('terminal', self.terminal_bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Store page reference for terminal bridge
        self.terminal_bridge.page = self.web_view.page()
        
        # Load the HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(current_dir, 'index.html')
        self.web_view.setUrl(QUrl.fromLocalFile(index_path))
        
        # Add web view to layout
        layout.addWidget(self.web_view)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 
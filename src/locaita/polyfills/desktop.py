import json
import subprocess, shutil


if shutil.which('hyprctl'):
    class Window:
        def __init__(self, win):
            [self.width, self.height] = win['size']
            [self.top, self.left] = win['at']
            self.isMinimized = not win['fullscreen']
            self.isMaximized = not self.isMinimized

    def getWindowsWithTitle(title: str):
        return [Window(win) for win in json.loads(
            subprocess.run(['hyprctl', 'clients', '-j']).stdout.decode(encoding='utf8')
        ) if win['title'] == title]
else:
    from pygetwindow import getWindowsWithTitle

__all__ = ['getWindowsWithTitle']

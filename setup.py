import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "sys", "PIL", "pillow_avif"], "includes": ["PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets"]}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ImageConverter",
    version="0.1",
    description="A simple image converter",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)

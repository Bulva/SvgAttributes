import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "gdal", "spectral"], "namespace_packages":["spectral"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

target = Executable(
    script="preview.py",
    base=base,
    compress=False,
    copyDependentFiles=True,
    appendScriptToExe=True,
    appendScriptToLibrary=False,
    icon="icon.ico"
    )

setup(
    name="Preview Generator",
    version="1.0",
    description="Preview Generator for Czech Globe",
    author="Petr Silhak",
    executables=[target]
    )






#!/usr/bin/env python3
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","gi","cairo","zlib","zipimport"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None


setup(  name = "pobtube",
        version = "0.1",
        description = "A gui for Youtube-dl",
        options = {"build_exe": build_exe_options},
        executables = [Executable("vd.py", base=base)])

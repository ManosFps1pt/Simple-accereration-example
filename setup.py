from cx_Freeze import setup, Executable

setup(
    name="demo",
    version="1.0",
    description="My Python App",
    executables=[Executable("v2.py")]
)

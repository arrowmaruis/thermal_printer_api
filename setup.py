from setuptools import setup, find_packages

setup(
    name="thermal_printer_api",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "python-escpos>=3.0.0",
        "pywin32;platform_system=='Windows'",
        "pillow>=8.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "thermal-printer=thermal_printer_api.main:main",
        ],
    },
    package_data={
        "thermal_printer_api.api": ["static/*"],
        "thermal_printer_api": ["*.json"],
    },
)
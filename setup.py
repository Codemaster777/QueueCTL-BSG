# setup.py - CONFIGURES THE PYTHON PACKAGE
from setuptools import setup, find_packages

setup(
    name='queuectl',
    version='2.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True, 
    install_requires=[
        'click',
        'tinydb',
        'Flask',
    ],
    entry_points={
        'console_scripts': [
            'queuectl = queuectl.cli:MainCLI',
        ],
    },
)
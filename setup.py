from setuptools import setup, find_packages

setup(
    name='coby',
    version="1.0",
    description="Concurrent build system",
    author="Martin Soderen",
    packages=find_packages(),
    include_package_data=True,
    entry_points = {'console_scripts': ['coby=coby.__main__:main'],}
)
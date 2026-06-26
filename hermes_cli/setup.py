from setuptools import setup

setup(
    name="hermes-cli",
    version="0.1.0",
    packages=["hermes_cli"],
    install_requires=["click>=8.1.0", "requests>=2.31.0"],
    entry_points={"console_scripts": ["hermes-cli=hermes_cli.cli:main"]},
)

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hubstaffutil",
    version="1.0.0",
    author="Cezanne Vahid",
    author_email="cezannevahid@gmail.com",
    description="Hubstaff utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "click",
        "pendulum",
        "pandas",
        "requests"
    ],
    include_package_data=True,
    packages=["src"],
    package_data={"src": ["data/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "hs_util = src.cli:cli",
        ],
    },
    python_requires=">=3.7")

import sys
from os import path

from setuptools import find_packages, setup

if sys.version_info < (3, 6, 0):
    sys.stderr.write("ERROR: You need Python 3.6 or later to use mypy.\n")
    exit(1)


here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Topic :: Database",
]


setup(
    name="psqlgml",
    author="Rowland Ogwara",
    author_email="rogwara@uchicago.edu",
    keywords="GraphML, psqlgraph, JSON schema",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    license="Apache 2.0",
    url="https://github.com/NCI-GDC/psqlgml",
    description="PSQL GraphML generator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "psqlgml": [
            "py.typed",
        ]
    },
    classifiers=classifiers,
    zip_safe=True,
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "attrs",
        "click",
        "colored",
        "dulwich",
        "graphviz",
        "Jinja2",
        "jsonschema",
        "PyYaml",
        "typing-extensions; python_version < '3.8'",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage[toml]",
            "flake8",
            "mypy",
            "pillow",
            "pre-commit",
            "pytest",
            "pytest-cov",
            "pytest-flask",
            "sphinx",
            "sphinx_rtd_theme",
            "sphinxcontrib-napoleon",
        ]
    },
    entry_points={"console_scripts": ["psqlgml = psqlgml.cli:app"]},
)

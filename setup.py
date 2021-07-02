from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="psqlgml",
    author="Rowland Ogwara",
    author_email="rogwara@uchicago.edu",
    keywords="GraphML, psqlgraph, JSON schema",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    url="",
    description="PSQL GraphML generator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    zip_safe=True,
    include_package_data=True,
    python_requires=">=3.8, <4",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "click",
        "graphviz",
        "Jinja2",
        "jsonschema",
        "PyYaml",
        "gdcdictionary @ git+https://github.com/NCI-GDC/gdcdictionary.git@2.4.0#egg=gdcdictionary",
        "biodictionary @ git+ssh://git@github.com/NCI-GDC/biodictionary.git@0.4.0#egg=biodictionary",
    ],
    extras_require={
        "dev": [
            "black",
            "coverage[toml]",
            "flake8",
            "pre-commit",
            "pytest",
            "pytest-cov",
            "pytest-flask",
            "sphinx",
            "sphinx_rtd_theme",
            "sphinxcontrib-napoleon",
        ]
    },
    entry_points={"console_scripts": ["psqlgml = psqlgml.cli:main"]},
)

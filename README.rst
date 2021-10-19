|ci|

Summary
-------
Sample data generation is a common step used for testing and verifying new and existing features that make use of the data commons dictionary. Without validation tools, this step can be super hard and prone to errors. This project aims to provide tooling that helps with generating and visualizing sample data. It is dictionary agnostic, so should work for any given gdc compatible dictionary.

Sample data graphs are represented using a customized GraphML_ format which can be represented in either json or yaml files. This projects provides tools for creating this schema based on selected dictionary and validating data that is targeting this schema.

Goals
-----
psqlgml aims to provide the following for projects that makes use of psqlgraph_:

1. test data validation and visualization
2. test data schema that can be integrated with IDE's for easier test data generation
3. randomized test data generation based on user requirements
4. provide data structures and functions for use in external projects
5. provide alternate implementation for loading dictionary with better type checking

Requirements
------------
* Python3.6+
* graphviz_ (used for visualization)

Installation
------------
from pypi

.. code-block:: bash

    $ pip install psqlgml

Quick Start
-----------
Command Line
++++++++++++
.. code-block:: bash

    # install
    $ pip install psqlgml

    # validate install
    $ psqlgml --help

    # generate internal schema to aid validation
    $ psqlgml generate -v 2.4.0 -n test_dictionary

    # validation
    $ psqlgml validate --help

    # visualize
    $ psqlgml visualize --help

API
+++
.. code-block:: python

    import psqlgml

    # load the default dictionary
    dictionary: psqlgml.Dictionary = psqlgml.load(version="2.3.0")


GML Schema
----------
This is a customized GraphML_ format based on JSON schema. It allows graphs to be represented as a set of nodes and edges. The schema makes it possible to validate a sample data.

.. code-block:: yaml

    unique_field: node_id
    nodes:
      - label: program
        node_id: p_1
        name: SM-KD
      - label: project
        node_id: pr_1
    edges:
      - src: p_1
        dst: pr_1
        label: programs

This example creats two nodes ``Program`` and ``Project`` that are linked together using the ``node_id`` property. The name of the edge connecting them is ``programs``

Schema Generation
-----------------
psqlgml can be used to generate dictionary specific schemas using exposed command line scripts. By default, gdcdictionary_ is assumed but parameters can be updated to work with a different project.

Generate schema using version 2.4.0 of the gdcdictionary

.. code-block::

    psqlgml generate -v 2.4.0 -n gdcdictionary

The generated schema can be used for validating sample data. It can also be added to IDEs like PyCharm for intellisense while creating sample data.

Sample Data Validation
----------------------
.. code-block::

    $ psqlgml validate -f sample.yaml --data-dir <resource dir> -d <dictionary name> -v <dictionary version>

The following validations are currently supported:

* JSON Schema Validation
* Duplicate Definition Validation
* Undefined Link Validation
* Association Validation

JSON Schema Validation
++++++++++++++++++++++
Checks the sample data is compliant with the dictionary. It validates things like:
* properties that are not allowed on a node
* property values not allowed on a property
* Invalid enum value
* Invalid/unsupported node types

Duplicate Definition Validation
+++++++++++++++++++++++++++++++
Raises an error whenever a unique id is used for more than one node

Undefined Link Validation
+++++++++++++++++++++++++
This is raised as a warning, since it is very possible to link to nodes not defined with the sample data. For example, appending data to an existing database.

Association Validation
++++++++++++++++++++++
Raises an error whenever an edge exists between nodes that the dictionary does not define an edge for.

.. |ci| image:: https://app.travis-ci.com/NCI-GDC/psqlgml.svg?token=5s3bZRahNJnkspYEMwZC&branch=master
    :target: https://app.travis-ci.com/github/NCI-GDC/psqlgml/branches
    :alt: build
.. |action| image:: https://img.shields.io/github/workflow/status/kulgan/psqlgml/psqlgml-ci
    :target: https://github.com/kulgan/psqlgml/actions
    :alt: psqlgml ci
.. _graphviz: https://graphviz.org/
.. _GraphML: http://graphml.graphdrawing.org/primer/graphml-primer.html
.. _gdcdictionary: https://github.com/NCI-GDC/gdcdictionary
.. _psqlgraph: https://github.com/NCI-GDC/psqlgraph

PsglGraph Mocking Tools
=======================
|ci|

A collection of api and tools for working with psqlgraph GraphML data

Requirements
------------
* Python3.6+
* dot

Features
--------
* GraphML Data Schema
* GraphML Data Validation
* GraphML Data Visualizer

Install
-------
Clone and install

.. code-block:: bash
    $ git clone git@github.com:NCI-GDC/psqlgml.git
    $ cd psqlgml
    $ pip install .

Schema Generation
-----------------
psqlgraph sample data can be described in a simple json or yaml file with entries for nodes and edges.
This project provides a schema that can be used to validate the sample data. The sample data is always
dependent on the target model dictionary (gdcdictionary or biodictionary)::

    nodes:
        - label: case
          submitter_id: c1
    edges:
        - src: p1
          dst: c1

.. code-block::

    $ psqlgml generate --help
      Usage: psqlgml generate [OPTIONS]

      Generate schema based on currently installed dictionaries

      Options:
        -o, --output-dir PATH        Output directory to store generated schema
        -d, --dictionary [GDC|GPAS]  Dictionary to generate schema for
        --help                       Show this message and exit.


.. |ci| image:: https://app.travis-ci.com/NCI-GDC/psqlgml.svg?token=5s3bZRahNJnkspYEMwZC&branch=master
    :target: https://app.travis-ci.com/github/NCI-GDC/psqlgml/branches
    :alt: build

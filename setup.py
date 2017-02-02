# -*- coding: utf-8 -*-

"""
Prepare bnm Python package for setup.
"""

import shutil
from setuptools import setup, find_packages

requirements = (
    'numpy',
    'scipy',
    'scikit-learn',
    'matplotlib',
    'trimesh',
    'anytree',
    'Pegasus',
    'h5py',
    'pytest',
    'Cython',
    'gdist',
)

setup(
    name="bnm",
    description="Brain Network Models - Reconstruction tool from structural MR scans",
    packages=find_packages(),
    version="0.1",
    license="Apache 2.0",
    author="BNM Team",
    install_requires=requirements,
)

shutil.rmtree('bnm.egg-info', True)

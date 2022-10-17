#!/usr/bin/env python

from distutils.core import setup
with open("readme.md", "r") as file:
    long_description = file.read()
setup(name='trisigma',
      version='1.0.0',
      description='trisigma engine',
      author='Arda Gok',
      author_email='ardagkmhs@gmail.com',
      long_description_content_type="text/markdown",
      long_description=long_description,
      keywords=['python', 'algo-trading', 'finance', 'stocks', 'crypto', 'market'],
      packages=['trisigma'],
      package_dir={'trisigma':'src'},
      install_requires=['numpy', 'pandas', 'binance-connector', 'requests'],

     )

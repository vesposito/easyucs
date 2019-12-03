#!/usr/bin/env python

import glob
import os
import pathlib
from setuptools import setup, find_packages, findall

def relative_iglob(root, glob_, recursive=None):
    """Yield setuptools-compatible POSIX paths matching a glob relative to a
    root.
    """
    fullglob = os.path.join(root, glob_)
    for path in glob.iglob(fullglob, recursive=recursive):
        yield pathlib.PurePosixPath(path).relative_to(root).as_posix()

setup(name='EasyUCS',
      version='0.9.4',
      description='A toolbox to help deploy and manage Cisco UCS devices',
      author='Vincent Esposito',
      author_email='vesposit@cisco.com',
      url='https://github.com/vesposito/easyucs',
      packages=find_packages(),
      package_data={
          'easyucs':
              list(relative_iglob('easyucs/', 'schema/**/*', recursive=True)) +
              list(relative_iglob('easyucs/', 'static/**/*', recursive=True)) +
              list(relative_iglob('easyucs/', 'templates/**/*', recursive=True)),
          },
      scripts=findall('easyucs/scripts/'),
      install_requires=[
          'paramiko >= 2.6.0',
          'imcsdk >= 0.9.7',
          'jsonschema >= 3.1.1',
          'python-docx >= 0.8.10',
          'requests >= 2.22.0',
          'ucsmsdk >= 0.9.8',
          'ucscsdk >= 0.9.0.1',
          'matplotlib >= 3.1.1',
          'networkx >= 2.4',
          'Pillow >= 6.2.1',
          'netaddr >= 0.7.19',
          'pyyaml >= 5.1.2',
          'packaging >= 19.0',
          'Flask >= 1.1.1',
          'scipy >= 1.3.1',
          ],
      classifiers=[
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
          ],
      )

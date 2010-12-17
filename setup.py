import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except IOError:
    README = CHANGES = ''

install_requires=['setuptools', 'pyramid', 'zope.interface', 'zope.proxy']
test_requires = ['zope.testing']

__version__ = "0.1"

setup(name='composite.traverser',
      version=__version__,
      description='Pluggable traverser for Pyramid',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "License :: BSD-Like",
      ],
      url="http://github.com/avnik/composite.traverser/",
      author="Alexander V. Nikolaev",
      author_email="avn@daemon.hole.ru",
      license="BSD-derived",
      packages=find_packages(),
      namespace_packages = ['composite', 'composite.traverser'],
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      tests_require= test_requires,
      extras_require = {
          'test': test_requires,
      },
)


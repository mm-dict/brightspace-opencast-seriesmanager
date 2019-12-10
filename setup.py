
from setuptools import setup, find_packages
from seriesmanager.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='seriesmanager',
    version=VERSION,
    description='Manage OpenCast Series with Ufora interfacing',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Multimedia',
    author_email='multimedia@ugent.be',
    url='https://github.ugent.be/Onderwijstechnologie-record/ufora-opencast-seriesmanager',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'seriesmanager': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        seriesmanager = seriesmanager.main:main
    """,
)

from setuptools import setup, find_packages

setup(
    name='spice_tools',
    version='1.0',
    packages=['spice_tools',
              'spice_tools.mosaics'],
    url='https://gitlab.esa.int/MarcelStefko/SpiceTools/',
    license='Proprietary ESA internal code - reuse outside ESA not allowed without explicit permission.',
    author='Marcel Stefko',
    author_email='marcel.stefko@esa.int',
    description=('Tools for working with MAPPS and Spice, '
                 'e.g. manipulating timestamps, analyzing power consumption, '
                 'and generating mosaic instructions.'),
    test_suite='tests',
    install_requires=[
        'numpy>=1.13.3',
        'six>=1.11.0',
        'matplotlib>=2.1.0',
        'iso8601>=0.1.12',
        'spiceypy>=2.1.0',
        'shapely',
        'pandas>=0.21.0']
)

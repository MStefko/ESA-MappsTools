from setuptools import setup, find_packages

setup(
    name='SpiceTools',
    version='0.1',
    packages=['', 'tests', 'mosaics'],
    url='https://gitlab.esa.int/MarcelStefko/SpiceTools/',
    license='Proprietary ESA internal code - reuse outside ESA not allowed without explicit permission.',
    author='Marcel Stefko',
    author_email='marcel.stefko@esa.int',
    description='',
    test_suite='tests',
    install_requires=['numpy','six','matplotlib','iso8601','spiceypy','shapely','pandas']
)

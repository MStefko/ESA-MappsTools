from setuptools import setup

setup(
    name='SpiceTools',
    version='0.1',
    packages=['', 'tests', 'mosaics'],
    url='https://gitlab.esa.int/MarcelStefko/SPICE_tools/',
    license='Proprietarycode ',
    author='Marcel Stefko',
    author_email='marcel.stefko@esa.int',
    description='',
    test_suite='tests',
    install_requires=['numpy','six','matplotlib','iso8601','spiceypy']
)

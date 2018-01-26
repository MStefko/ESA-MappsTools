from setuptools import setup, find_packages

setup(
    name='SpiceTools',
    version='0.1',
    url='https://gitlab.esa.int/MarcelStefko/SPICE_tools/',
    license='Proprietarycode ',
    author='Marcel Stefko',
    author_email='marcel.stefko@esa.int',
    description='',
    test_suite='tests',
    install_requires=['numpy','six','matplotlib','iso8601','spiceypy','shapely','pandas'],
    packages = find_packages(),
    package_data = {'': ['tests/*.itl']},
    include_package_data = True
)

import os
from setuptools import setup, find_packages

def get_all_filepaths_including_subdirs(path):
    paths = []
    for path, subdirs, files in os.walk(path):
        for name in files:
          paths.append(os.path.join(path, name))
    return paths
    
def get_package_version(here):
    import re
    filename = os.path.join(here, "blumycellium", "_version.py")
    with open(filename) as f:
        try:
            line = f.readlines()[0]
        except:
            raise RuntimeError("Impossible to read version name: %s" % filename)
    
    reg = r"^__version__\s*=\s*['\"]([^'\"]+)['\"]"
    res = re.search(reg, line, re.M)
    if res:
        version = res.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (filename,))

    return version.strip()

def read_file_content(here, name):
    with open(os.path.join(here, name)) as f:
        data = f.read()
    return data

here = os.path.abspath(os.path.dirname(__file__))

README = read_file_content(here, 'README.md')
CHANGES = read_file_content(here, 'CHANGES.md')
VERSION = get_package_version(here)

package_data = []
# package_data += get_all_filepaths_including_subdirs(here + '/blumycellium/locale')
# package_data += get_all_filepaths_including_subdirs(here + '/blumycellium/configuration_json')

requires = [
    "pyArango>=1.3.5"
]

setup(name='blumycellium',
      version=VERSION,
      description='blumycellium',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Tariq Daouda',
      author_email='tariq@bluwr.com',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      package_data={'blumycellium': package_data},
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="blumycellium",
      entry_points="""\
      [paste.app_factory]
      main = blumycellium:main
      """,
      )

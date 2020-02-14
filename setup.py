import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="waiwera-credo",
    version="2.0.3",
    author="Waiwera Project",
    author_email="waiwera.project@gmail.com",
    description="Fork of CREDO computational model benchmarking toolkit, for use with the Waiwera geothermal flow simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://waiwera.github.io",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
    install_requires=['future', 'matplotlib', 'scipy', 'Pillow',
                      'h5py', 'Shapely', 'docutils', 'reportlab']
)

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pySTEP",
    version="0.2.1",
    author="Kerim Charfi",
    author_email="kerim.charfi@ionix.cc",
    description="A lightweight, expandable, pure python step parsing package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kerimcharfi/pySTEP",
    packages=["pySTEP", "pySTEP.paths"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
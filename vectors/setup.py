import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vectors", # Replace with your own username
    version="0.0.6",
    author="Kerim Charfi",
    author_email="kerim.charfi@ionix.cc",
    description="A lightweight, expandable, pure python numpy wrapping package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
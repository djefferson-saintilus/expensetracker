from setuptools import setup, find_packages

setup(
    name="expense-tracker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "bcrypt",
    ],
    entry_points={
        "console_scripts": [
            "expense=expense:main",
        ],
    },
    author="Djefferson Saintilus",
    author_email="kylejeffleo@gmail.com",
    description="A simple expense tracker application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/djefferson-saintilus/expensetracker",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

import re
from setuptools import setup, find_packages


def get_long_description():
    with open("README.rst") as readme:
        return readme.read()


def get_version():
    with open("sans/info.py") as f:
        return re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(
            1
        )


def get_requires():
    with open("requirements.txt") as f:
        return f.read().splitlines()


extras_require = {"docs": ["sphinx==1.8.3"]}


if __name__ == "__main__":
    setup(
        name="sans",
        version=get_version(),
        description="Synchronous / Asynchronous NationStates API wrapper for Python",
        long_description=get_long_description(),
        long_description_content_type="text/x-rst",
        author="Zephyrkul",
        author_email="zephyrkul@outlook.com",
        url="https://github.com/zephyrkul/sans",
        packages=["sans"],
        license="MIT",
        python_requires=">=3.6.0,<3.8",
        install_requires=get_requires(),
        extras_require=extras_require,
        entry_points={"console_scripts": ["sans=sans.__main__:main"]},
        classifiers=[
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: MIT License",
            "Intended Audience :: Developers",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Topic :: Software Development :: Libraries",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Utilities",
        ],
    )

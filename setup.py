# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="ymbotpy",
    version='1.0.0.dev',
    author="yiming",
    author_email="1790233968@qq.com",
    description="QQ robot webhook server using Python 3",
    long_description=open("README.md", 'r',encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://github.com/HG-ha/ym-qq-botpy",
    packages=find_packages(),
    license="YiMing",
    install_requires=["aiohttp>=3.7.4,<4", 
                      "PyYAML", 
                      "APScheduler",
                      "cryptography>=43.0.0",
                      "fastapi>=0.115.0",
                      "multidict",
                      "uvicorn"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ],
)

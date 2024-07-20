#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="openobserve-python-handler",
    version="1.0.3",
    description="Logging handler to send logs to your OpenObserve service",
    keywords="logging handler",
    author="digithrone",
    maintainer="digithrone",
    mail="info@digithrone.com",
    url="https://github.com/digithrone/openobserve-python-handler",
    license="Apache License 2",
    packages=find_packages(),
    install_requires=[
        "requests>=2.27.0",
        "protobuf>=3.20.2"
    ],
    extras_require={
        "opentelemetry-logging": ["opentelemetry-instrumentation-logging==0.46b0"]
    },
    test_requires=["future"],
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
    ],
)

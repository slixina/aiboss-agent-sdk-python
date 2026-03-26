from setuptools import find_packages, setup


setup(
    name="aiboss-sdk",
    version="0.1.0",
    description="AI Boss Platform SDK for Python",
    author="AI Boss Team",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ]
    },
)

from setuptools import setup, find_packages

setup(
    name="reup",
    version="1.0.0",
    description="A desktop application for monitoring Best Buy Canada product availability",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "plyer>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "reup=reup.run:main",
        ],
    },
    extras_require={
        'test': [
            'pytest>=6.0',
            'pytest-cov',
            'pytest-timeout',
            'pytest-mock',
            'pytest-asyncio',
            'black',
            'flake8'
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 
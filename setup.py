import setuptools

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

requires = [
    "alipay-sdk-python>=3.3.398",
    "pendulum>=2.1.2",
    "requests>=2.25.1",
    "pycryptodome>=3.9.9",
]

setuptools.setup(
    name="easy-pay",
    version="0.0.1",
    author="Steven Wang",
    author_email="brightstar8284@icloud.com",
    description="Easier integration with WeChat pay and Alipay.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StevenLianaL/easy-pay",
    packages=setuptools.find_packages(),
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

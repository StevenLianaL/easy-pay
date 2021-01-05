import setuptools

with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="easy-pay",
    version="0.0.1",
    author="Steven Wang",
    author_email="brightstar8284@icloud.com",
    description="Easier integration with WeChat pay and Alipay.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="git@github.com:StevenLianaL/easy-pay.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)

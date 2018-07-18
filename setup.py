import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="PortfolioOptimizer",
    version="1.0.0",
    author="WLMike",
    author_email="wlmike@gmail.com",
    description="Оптимизация долгосрочного портфеля акций",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WLM1ke/PortfolioOptimizer",
    packages=setuptools.find_packages(),
    classifiers=("Programming Language :: Python :: 3",),
)

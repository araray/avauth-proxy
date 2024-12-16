from setuptools import setup, find_packages

setup(
    name="avauth_proxy",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask",
        "Authlib",
        "prometheus_client",
        "gunicorn",
        "jinja2",
        "uuid",
        "python-json-logger",
        "tomli",
        "tomli-w",
        "pytest",
        "requests",
        "pytest-mock",
        "requests-cache",
        "requests-oauthlib",
        "watchdog",
    ],
)


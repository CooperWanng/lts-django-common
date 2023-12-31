from setuptools import setup, find_packages

require = [
    "django==3.2.11",
    "django-filter==21.1",
    "djangorestframework==3.12.0",
    "django-crum==0.7.9",
    "drf-yasg==1.21.3",
    "django-cors-headers==3.13.0",
    "mysqlclient==1.4.6"
]

setup(
    name="lucommon",
    version="1.0.4",
    install_requires=require,
    packages=find_packages(),
    zip_safe=True
)

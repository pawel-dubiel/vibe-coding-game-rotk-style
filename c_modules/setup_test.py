from setuptools import setup, Extension

module = Extension('test_extension', sources=['c_modules/test_extension.c'])

setup(
    name='test_extension',
    version='1.0',
    description='Test C extension',
    ext_modules=[module]
)

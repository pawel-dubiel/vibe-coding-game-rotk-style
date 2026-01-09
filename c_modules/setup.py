from setuptools import setup, Extension

module = Extension('c_algorithms', sources=['c_modules/c_algorithms.c'])

setup(
    name='c_algorithms',
    version='1.0',
    description='Optimized C algorithms for Medieval Hex Strategy Game',
    ext_modules=[module]
)

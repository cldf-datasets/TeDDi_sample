from setuptools import setup


setup(
    name='cldfbench_100LC',
    py_modules=['cldfbench_100LC'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            '100LC=cldfbench_100LC:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)

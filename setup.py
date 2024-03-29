from setuptools import setup


setup(
    name='cldfbench_TeDDi_sample',
    py_modules=['cldfbench_TeDDi_sample'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'TeDDi_sample=cldfbench_TeDDi_sample:Dataset',
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

from setuptools import find_packages, setup


# setup script
if __name__ == '__main__':

    # run setup
    setup(

        # standard info
        name='litai',
        version='0.2.9',
        description='ai-powered literature search',
        author='Mike Powell PhD',
        author_email='mike@lakeslegendaries.com',
        license='MIT License',

        # packages to include
        packages=find_packages(),

        # requirements
        install_requires=[
            'fastapi',
            'mysqlclient',
            'nptyping',
            'numpy',
            'pandas',
            'pyyaml',
            'retry',
            'sklearn',
            'sqlalchemy',
            'uvicorn',
            'vhash',
        ],
        python_requires='>=3.8',

        # urls
        project_urls={
            "Documentation": "https://lakes-legendaries.github.io/litai/",
            "GitHub": "https://github.com/lakes-legendaries/litai/",
            "Bug Tracker": "https://github.com/lakes-legendaries/litai/issues",
        },

        # classifiers
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    )

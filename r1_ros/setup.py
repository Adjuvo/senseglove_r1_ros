from setuptools import setup
import os
from glob import glob

package_name = 'r1_ros'

setup(
    name=package_name,
    version='0.1.0',
    description='R1 interaction nodes',
    url='https://senseglove.com',
    author='Akshay Radhamohan Menon',
    author_email='akshay@senseglove.com',
    license='MIT',
    packages=[
        package_name,
        f'{package_name}.haptics',
        f'{package_name}.main',
    ],
    package_dir={'': '.'},
    package_data={f'{package_name}.haptics': ['tacto_generic.bin']},
    install_requires=[
        'setuptools',
        'SG_API',
        'touchlab-comm-py',
    ],
    extras_require={
        'test': ['pytest'],
    },
    zip_safe=True,
    entry_points={
        'console_scripts': [
            # haptics
            'force_slider_node = r1_ros.haptics.force_slider:main',
            # main
            'r1_manager = r1_ros.main.r1_manager:main',
        ],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
)
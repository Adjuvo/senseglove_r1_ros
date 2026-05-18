from setuptools import setup
import os
from glob import glob

package_name = 'r1_interaction'

setup(
    name=package_name,
    version='0.0.1',
    description='R1 interaction nodes',
    url='https://senseglove.com',
    author='Akshay Radhamohan Menon',
    author_email='akshay@senseglove.com',
    license='MIT',
    packages=[
        package_name,
        f'{package_name}.configs.robot_hand_mapper',
        f'{package_name}.haptics',
        f'{package_name}.main',
    ],
    package_dir={'': '.'},
    install_requires=[
        'setuptools',
        'rclpy',
        'std_msgs',
        'r1_msgs',
        'SG_API',
    ],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            # haptics
            'force_slider_node = r1_interaction.haptics.force_slider:main',
            # main
            'r1_manager = r1_interaction.main.r1_manager:main',
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
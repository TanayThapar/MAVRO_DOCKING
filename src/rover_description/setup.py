from setuptools import setup
import os
from glob import glob

package_name = 'rover_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        #Include launch files
        (os.path.join('share', package_name, 'urdf'), glob('urdf/**/*', recursive=True)),

        #Include urdf
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),

        #Include config
        (os.path.join('share', package_name, 'config'), glob('config/*')),

        #Include model
        (os.path.join('share', package_name, 'model'), glob('model/*')),

        #Include rviz
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),

        #Include worlds
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rover',
    maintainer_email='rover@todo.todo',
    description='Rover description package',
    license='TODO',
    entry_points={
        'console_scripts': [
            'aruco_detector = rover_description.aruco_detector_node:main',
            'dock_pid_controller = rover_description.dock_pid_controller:main',
        ],
    },
)
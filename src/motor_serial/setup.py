import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'motor_serial'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='koushik',
    maintainer_email='koushik@todo.todo',
    description='Motor serial control with teleop and joystick',
    license='MIT',  # change if you want another license
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'serial_bridge = motor_serial.serial_bridge:main',
            'twist_to_motor = motor_serial.twist_to_motor:main',
            'arrow_teleop = motor_serial.arrow_teleop:main',
            'ps5_drive = motor_serial.ps5_drive:main',
	    'motor_controller = motor_serial.motor_controller:main',
        ],
    },
)


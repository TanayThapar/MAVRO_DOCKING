from setuptools import find_packages, setup

package_name = 'camera_controll'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rover',
    maintainer_email='rover@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
	'rover_camera_node = camera_controll.rover_camera_node:main',
	'yolo_subscriber_node = camera_controll.yolo_subscriber_node:main',
        ],
    },
)

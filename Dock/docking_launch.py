from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Path to your parameter files
    docking_params = os.path.join(get_package_share_directory('your_package'), 'config', 'aruco_docking.yaml')

    return LaunchDescription([
        # 1. Start the ArUco Docking Node with your YAML params
        Node(
            package='your_package',
            executable='aruco_docking_node',
            name='aruco_docking_node',
            parameters=[docking_params]
        ),
        
        # 2. Start AMCL (if you want it running simultaneously)
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            parameters=[os.path.join(get_package_share_directory('your_package'), 'config', 'docking.yaml')]
        )
    ])
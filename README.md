# YELLOW ROVER: ArUco-Based Autonomous Docking

## Problem Statement

The Yellow Rover, a ROS 2-based differential drive autonomous mobile robot, requires a robust mechanism for autonomous docking. The objective is to design and implement a perception and control pipeline that enables the rover to identify a specific docking station using an ArUco marker, navigate toward it, and precisely align itself for docking. 

This capability must integrate seamlessly with the rover's existing ROS 2 software stack within the `yellowbot_ws` workspace, utilizing its existing sensor suite, edge AI capabilities, and navigation stack.

## Objectives

1. **Marker Detection & Pose Estimation**: 
   - Utilize the rover's existing `/rover/camera/image_raw` feed, provided by the `camera_controll` package, to continuously scan for the target ArUco marker.
   - Accurately estimate the 6D pose (translation and rotation) of the marker relative to the camera frame using OpenCV, augmenting the existing edge AI pipeline (which currently utilizes YOLOv8).

2. **Coordinate Transformation**: 
   - Broadcast the detected ArUco marker's pose to the ROS 2 `tf2` tree. 
   - Calculate the required goal pose for the rover in the `map` or `odom` frame to align the `base_footprint` perfectly with the docking station.

3. **Autonomous Navigation & Alignment**: 
   - **Far-field approach**: If the marker is detected from a distance, send a goal to the navigation stack to bring the rover within close proximity of the dock.
   - **Near-field docking**: Once in close proximity (e.g., < 1.0 meter), switch to a custom precise control loop publishing directly to `/cmd_vel`. This will interface directly with the `cpp_motor` or `motor_serial` packages (which translate commands for the ESP32 and DDSM115 motors) to handle final alignment, correcting for small lateral and angular offsets until the dock is successfully engaged.

## System Architecture Context

This feature builds upon the existing architecture detailed in the `yellowbot_ws` workspace:

- **Hardware Control Layer**: The docking logic will publish to `/cmd_vel`, which will be translated into JSON payloads for the ESP32 by the `cpp_motor` (or `motor_serial`) package.
- **Perception Layer**: A new `aruco_docking` node will be added alongside the `yolo_subscriber_node.py` in the `camera_controll` package, intercepting raw frames for ArUco detection.
- **State Estimation**: Relies on the `ekf_node` from `rover_description` fusing IMU and odometry data for smooth local docking maneuvers.
- **Simulation**: The system should be fully testable within the `dream_world` Gazebo simulation environments before deployment on the Raspberry Pi 5 compute node.

## Demonstration

You can view a demonstration of the Yellow Rover's docking process here:

[▶ Watch Docking Demo (dock1.webm)](https://drive.google.com/file/d/1JZ9EM6EXhnc9GdIOiNgpic_JoCu6y96l/view?usp=sharing)

## Expected Workflow

1. An interrupt or behavior tree condition triggers the "Return to Dock" phase (e.g., low battery).
2. The rover navigates to the general known vicinity of the dock using standard Nav2/SLAM navigation.
3. The camera detects the ArUco marker and estimates its pose.
4. The rover enters the visual servoing phase, utilizing precise `/cmd_vel` inputs to align itself.
5. The rover drives forward until docking is physically confirmed.

## Prerequisites

- ROS2 Humble / Jazzy
- Gazebo Ignition
- Colcon build tools
- OpenCV with ArUco support

## How to Run

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TanayThapar/MAVRO_DOCKING.git
   cd MAVRO_DOCKING
   ```

2. **Source the environment and build:**
   ```bash
   source /opt/ros/<distro>/setup.bash
   colcon build
   source install/setup.bash
   ```

3. **To run gazebo and aruco detector:**
   ```bash
   ros2 launch rover_description spawn_rover.launch.py
   ```

4. **To run rviz:**
   ```bash
   ros2 launch rover_description display.launch.py
   ```

5. **To run pid controllers:**
   ```bash
   ros2 launch rover_description pid.launch.py
   ```

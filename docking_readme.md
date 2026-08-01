# YELLOW ROVER: ArUco-Based Autonomous Docking

## Problem Statement

The Yellow Rover, a ROS 2-based differential drive platform developed for frontier exploration, now requires a robust mechanism for autonomous docking. The objective is to design and implement a perception and control pipeline that enables the rover to identify a specific docking station using an ArUco marker, navigate toward it, and precisely align itself for docking. 

This capability must integrate seamlessly with the rover's existing ROS 2 navigation stack (Nav2) and sensor suite.

## Objectives

1. **Marker Detection & Pose Estimation**: 
   - Utilize the rover's existing `/rover/camera/image_raw` feed (via `/dev/video0`) to continuously scan for the target ArUco marker.
   - Accurately estimate the 6D pose (translation and rotation) of the marker relative to the camera frame using OpenCV.

2. **Coordinate Transformation**: 
   - Broadcast the detected ArUco marker's pose to the ROS 2 `tf2` tree. 
   - Calculate the required goal pose for the rover in the `map` or `odom` frame to align the `base_link` perfectly with the docking station.

3. **Autonomous Navigation & Alignment**: 
   - **Far-field approach**: If the marker is detected from a distance, send a `nav2_msgs/action/NavigateToPose` goal to Nav2 to bring the rover within close proximity of the dock.
   - **Near-field docking**: Once in close proximity (e.g., < 1.0 meter), switch to a custom precise control loop publishing directly to `cmd_vel` to handle final alignment, correcting for small lateral and angular offsets until the dock is successfully engaged.

## System Architecture Context

This feature builds upon the existing architecture detailed in the `CEAM-MITBLR` repositories and the foundational Yellow Rover workspace:

- **Perception**: A new `aruco_docking` node will subscribe to the camera feed published by the existing `camera_controll` node.
- **Actuation**: The docking logic will interface with the `motor_serial` and `cpp_motor` packages by sending `cmd_vel` commands during the final approach.
- **Simulation**: The system should be testable within the `dream_world` Gazebo environment, where a simulated docking station with an ArUco texture can be spawned.

## Expected Workflow

1. The rover performs standard Wavefront Frontier Detection to explore the map.
2. An interrupt or behavior tree condition triggers the "Return to Dock" phase (e.g., low battery).
3. The rover navigates to the general known vicinity of the dock using Nav2.
4. The camera detects the ArUco marker.
5. The rover enters the visual servoing phase, aligning itself and driving forward until docking is confirmed.

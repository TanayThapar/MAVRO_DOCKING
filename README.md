# Yellow Rover

## How to Run

### Prerequisites
- ROS2 Humble / Jazzy
- Gazebo Ignition
- Colcon build tools

### Steps
```bash
git clone https://github.com/TanayThapar/MAVRO_DOCKING.git
cd MAVRO_DOCKING
```
```bash
source /opt/ros/<distro>/setup.bash
```
```bash
colcon build
source install/setup.bash
```
### To run gazebo, aruco detector and controller
```bash
ros2 launch rover_description spawn_rover.launch.py
```

### To run rviz
```bash
ros2 launch rover_description display.launch.py
```

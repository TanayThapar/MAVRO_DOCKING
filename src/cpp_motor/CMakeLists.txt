cmake_minimum_required(VERSION 3.8)
project(cpp_motor)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)  # <-- This was missing

# --- Build motor_control_node ---
add_executable(motor_control_node src/motor_control_node.cpp)

ament_target_dependencies(motor_control_node
  "rclcpp"
  "geometry_msgs"
  "sensor_msgs"  # This was in the wrong place
)

target_link_libraries(motor_control_node pthread)

# --- Build ps5_teleop_node ---
add_executable(ps5_teleop_node src/ps5_teleop_node.cpp)

ament_target_dependencies(ps5_teleop_node
  "rclcpp"
  "sensor_msgs"
  "geometry_msgs"
)

# --- Install both executables ---
install(TARGETS
  motor_control_node
  ps5_teleop_node
  DESTINATION lib/${PROJECT_NAME}
)

# Linting and testing
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

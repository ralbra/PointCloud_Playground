cmake_minimum_required(VERSION 3.8)
project(grid_fusion)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(grid_map_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rcl_interfaces REQUIRED)

add_executable(grid_fusion_node src/grid_fusion_node.cpp)
target_include_directories(grid_fusion_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(grid_fusion_node
  rclcpp nav_msgs grid_map_msgs builtin_interfaces rcl_interfaces)

install(TARGETS grid_fusion_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()

  ament_add_gtest(test_fusion test/test_fusion.cpp)
  target_include_directories(test_fusion PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
  ament_target_dependencies(test_fusion nav_msgs grid_map_msgs builtin_interfaces)
endif()

ament_package()
cmake_minimum_required(VERSION 3.15)
project(MyShardsApp)

set(CMAKE_CXX_STANDARD 17)

# Add SHARDS directory (absolute or relative path)
add_subdirectory(SHARDS-cpp)

# Define your app
add_executable(my_app main.cpp)

# Link SHARDS
target_link_libraries(my_app PRIVATE Shards)

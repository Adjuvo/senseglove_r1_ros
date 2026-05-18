# Copyright (c) 2020 - 2026 SenseGlove

cmake_minimum_required(VERSION 3.16...3.25)

project(r1_bringup
        VERSION 0.0.1
        DESCRIPTION "Launch files for R1"
        HOMEPAGE_URL "https://senseglove.com"
        LANGUAGES NONE
        )

# Find dependencies
find_package(ament_cmake REQUIRED)

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
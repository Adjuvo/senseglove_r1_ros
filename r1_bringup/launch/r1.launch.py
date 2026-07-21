from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_simulation = LaunchConfiguration('use_simulation')
    num_gloves = LaunchConfiguration('num_gloves')

    launch_main_node = Node(
        package='r1_interaction',
        executable='r1_manager',
        name='r1_manager',
        parameters=[{
            'num_gloves': num_gloves,
            'use_simulation': use_simulation,
        }],
        output='screen',
    )
    return LaunchDescription([
        DeclareLaunchArgument('num_gloves', default_value='1'),
        DeclareLaunchArgument('use_simulation', default_value='false'),
        launch_main_node
    ])
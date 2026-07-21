from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('hand', default_value='left', description='left or right'),
        DeclareLaunchArgument('glove_id', default_value='73', description='R1 glove ID'),
        DeclareLaunchArgument('port', default_value='/dev/ttyACM0', description='TouchLab serial port'),

        Node(
            package='r1_interaction',
            executable='touchlab_haptic_node',
            name='touchlab_haptic_node',
            parameters=[{
                'hand': LaunchConfiguration('hand'),
                'glove_id': LaunchConfiguration('glove_id'),
                'port': LaunchConfiguration('port'),
            }],
            output='screen',
        ),
    ])
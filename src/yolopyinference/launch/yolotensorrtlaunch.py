import os
import launch
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """Launch the DNN Image encoder, TensorRT node and Yolov5 decoder node."""
    config = os.path.join(
        get_package_share_directory('yolopyinference_ros'),
        'config',
        'decoder_params.yaml'
    )

    launch_args = [
        DeclareLaunchArgument(
            'network_image_width',
            default_value='640',#960
            description='The input image width that the network expects'),
        DeclareLaunchArgument(
            'network_image_height',
            default_value='640',#544
            description='The input image height that the network expects'),
        DeclareLaunchArgument(
            'encoder_image_mean',
            default_value='[0.5, 0.5, 0.5]',
            description='The mean for image normalization'),
        DeclareLaunchArgument(
            'encoder_image_stddev',
            default_value='[0.5, 0.5, 0.5]',
            description='The standard deviation for image normalization'),
        DeclareLaunchArgument(
            'model_file_path',
            default_value='/myROS2/tmp/yolov5s.onnx',
            description='The absolute file path to the ONNX file'),
        DeclareLaunchArgument(
            'engine_file_path',
            default_value='/myROS2/tmp/yolov5s.plan',
            description='The absolute file path to the TensorRT engine file'),
        DeclareLaunchArgument(
            'input_tensor_names',
            default_value='["input_tensor"]',
            description='A list of tensor names to bound to the specified input binding names'),
        DeclareLaunchArgument(
            'input_binding_names',
            default_value='["images"]', #'["input_1"]'
            description='A list of input tensor binding names (specified by model)'),
        DeclareLaunchArgument(
            'input_tensor_formats',
            default_value='["nitros_tensor_list_nchw_rgb_f32"]',
            description='The nitros format of the input tensors'),
        DeclareLaunchArgument(
            'output_tensor_names',
            default_value='["output_tensor"]',
            description='A list of tensor names to bound to the specified output binding names'),
        DeclareLaunchArgument(
            'output_binding_names',
            default_value='["output0"]', #'["softmax_1"]'
            description='A  list of output tensor binding names (specified by model)'),
        DeclareLaunchArgument(
            'output_tensor_formats',
            default_value='["nitros_tensor_list_nhwc_rgb_f32"]',
            description='The nitros format of the output tensors'),
        DeclareLaunchArgument(
            'tensorrt_verbose',
            default_value='False',
            description='Whether TensorRT should verbosely log or not'),
        DeclareLaunchArgument(
            'force_engine_update',
            default_value='False',
            description='Whether TensorRT should update the TensorRT engine file or not'),
    ]

    # DNN Image Encoder parameters
    network_image_width = LaunchConfiguration('network_image_width')
    network_image_height = LaunchConfiguration('network_image_height')
    encoder_image_mean = LaunchConfiguration('encoder_image_mean')
    encoder_image_stddev = LaunchConfiguration('encoder_image_stddev')

    # TensorRT parameters
    model_file_path = LaunchConfiguration('model_file_path')
    engine_file_path = LaunchConfiguration('engine_file_path')
    input_tensor_names = LaunchConfiguration('input_tensor_names')
    input_binding_names = LaunchConfiguration('input_binding_names')
    input_tensor_formats = LaunchConfiguration('input_tensor_formats')
    output_tensor_names = LaunchConfiguration('output_tensor_names')
    output_binding_names = LaunchConfiguration('output_binding_names')
    output_tensor_formats = LaunchConfiguration('output_tensor_formats')
    tensorrt_verbose = LaunchConfiguration('tensorrt_verbose')
    force_engine_update = LaunchConfiguration('force_engine_update')


    encoder_node = ComposableNode(
        name='dnn_image_encoder',
        package='isaac_ros_dnn_encoders',
        plugin='nvidia::isaac_ros::dnn_inference::DnnImageEncoderNode',
        parameters=[{
            'network_image_width': network_image_width,
            'network_image_height': network_image_height,
            'image_mean': encoder_image_mean,
            'image_stddev': encoder_image_stddev,
        }],
        remappings=[('encoded_tensor', 'tensor_pub'), ('image', '/camera/color/image_raw')]
    )

    tensorrt_node = ComposableNode(
        name='tensor_rt_node',
        package='isaac_ros_tensor_rt',
        plugin='nvidia::isaac_ros::dnn_inference::TensorRTNode',
        parameters=[{
            'model_file_path': model_file_path,
            'engine_file_path': engine_file_path,
            'input_tensor_names': input_tensor_names,
            'input_binding_names': input_binding_names,
            'input_tensor_formats': input_tensor_formats,
            'output_tensor_names': output_tensor_names,
            'output_binding_names': output_binding_names,
            'output_tensor_formats': output_tensor_formats,
            'verbose': tensorrt_verbose,
            'force_engine_update': force_engine_update
        }])      


    # resize_node = ComposableNode(
    #     name='isaac_ros_resize',
    #     package='isaac_ros_image_proc',
    #     plugin='isaac_ros::image_proc::ResizeNode',
    #     parameters=[{
    #         'use_relative_scale': False,
    #         'height': 640,
    #         'width': 640,
    #     }]
    # )

    
    rclcpp_container = ComposableNodeContainer(
        name='yolo_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[
            encoder_node, tensorrt_node],
        output='screen',
    )


    yolo_decoder_node = Node(
        name='yolo_decoder_node',
        package='yolopyinference_ros',
        executable='YoloDecoder',
        parameters=[config],
        output='screen',
    )


    image_visualizer_node = Node(
            name='image_visualizer_node',
            package='yolopyinference_ros',
            executable='image_visualizer',
            output='screen',
    )
    
    rqt_node = Node(
            name='image_view',
            package='rqt_image_view',
            executable='rqt_image_view',
            arguments=['/processed_image']
    )



    final_launch_description = launch_args + [rclcpp_container] + [yolo_decoder_node] + [image_visualizer_node] + [rqt_node]
    return launch.LaunchDescription(final_launch_description)
from isaac_ros_tensor_list_interfaces.msg import TensorList
import numpy as np
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from scipy import special
import torch
#from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import String
from vision_msgs.msg import Detection2D
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import ObjectHypothesisWithPose
from pathlib import Path
from build.yolopyinference_ros.yolopyinference_ros.utils.YoloUtils import tensor_to_torch_array, select_device, non_max_suppression, scale_boxes, xyxy2xywh
# def tensor_to_torch_array(tensor):
#     shape = tuple(tensor.shape.dims)
#     x = None
#     if tensor.data_type == 9:  # float32
#         x = torch.frombuffer(bytearray(tensor.data), dtype=torch.float32)
#     elif tensor.data_type == 10:  # float64
#         x = torch.frombuffer(bytearray(tensor.data), dtype=torch.float64)
#     else:
#         print('Received tensor of incorrect type:', tensor.data_type)
#         return None
#     x = torch.reshape(x, shape)
#     return x

def decode(pred, params_config):
    # Convert Isaac ROS tensors to torch arrays
    pred = tensor_to_torch_array(pred)

    # Decode tensors into a set of detections
    conf_thres = params_config['conf_thres']
    iou_thres = params_config['iou_thres']
    max_det = params_config['max_det']
    classes = None
    agnostic_nms = False
    device = ''
    
    device = select_device(device)

    pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
    # pred = [cx, cy, w, h, conf, pred_cls(80)]
    detections_arr = Detection2DArray()


    for i, det in enumerate(pred):
        #print(len(det))
        if len(det):
            #(640, 640) is input dimensions expected by YOLOv5s network
            shape = torch.Size([640, 640])
            #(1280, 720) is image size from RealSense camera
            #print(det[:, :4])
            det[:, :4] = scale_boxes(shape, det[:, :4], (720, 1280, 3))

            
            for *xyxy, conf, cls in det:
                xywh = xyxy2xywh(torch.tensor(xyxy).view(1, 4)).view(-1)
                #xywh = xyxy
                print(xywh)
    
                obj = Detection2D()
                obj.bbox.size_x = float(xywh[2])
                obj.bbox.size_y = float(xywh[3])
                obj.bbox.center.position.x = float(xywh[0])
                obj.bbox.center.position.y = float(xywh[1])
                obj.id = str(int(cls))
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = str(int(cls))
                hyp.hypothesis.score = float(conf)
                obj.results.append(hyp)
                detections_arr.detections.append(obj)

    return detections_arr


class ROSYoloDecoderNode(Node):

    def __init__(self, name='yolo_decoder_node'):
        super().__init__(name)
        self.declare_parameters(
            namespace='',
            parameters=[
                ('conf_thres', rclpy.Parameter.Type.DOUBLE),
                ('iou_thres', rclpy.Parameter.Type.DOUBLE),
                ('max_det', rclpy.Parameter.Type.INTEGER)
            ])
    
        
        # Sanity check parameters
        self.params_config = {}
        param_names = ['conf_thres', 'iou_thres', 'max_det']

        for param_name in param_names:
            try:
                self.params_config[param_name] = self.get_parameter(
                    param_name).value
            except rclpy.exceptions.ParameterUninitializedException:
                self.params_config[param_name] = None


        if self.params_config['conf_thres'] is None:
            self.get_logger().warning('No confidence threshold specified. Assuming 0.55')
            self.params_config['conf_thres'] = 0.55

        if self.params_config['iou_thres'] is None:
            self.get_logger().warning('No IOU threshold specified. Assuming 0.45')
            self.params_config['iou_thres'] = 0.45

        if self.params_config['max_det'] is None:
            self.get_logger().warning('No maximum number of detections per image specified. Assuming 1000')
            self.params_config['max_det'] = 1000


        # Create the subscriber. This subscriber will subscribe to a TensorList message
        self.subscription_ = self.create_subscription(TensorList, 'tensor_sub',
                                                      self.listener_callback, 10)


        # Create the publisher. This publisher will publish a Detection2DArray message
        # to topic object_detections. The queue size is 10 messages.
        self.publisher_ = self.create_publisher(
            Detection2DArray, 'object_detections', 10)
        

    def listener_callback(self, msg):
        tensors = msg.tensors
    
        detections = decode(tensors[0], self.params_config)

        if detections is None:
            self.get_logger().error('Error decoding input tensors')
            return

        detections.header = msg.header

        for det in detections.detections:
            det.header = msg.header
            

        # Publish the message to the topic
        self.publisher_.publish(detections)

def main(args=None):
    try:
        rclpy.init(args=args)
        node = ROSYoloDecoderNode('yolo_decoder_node')
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
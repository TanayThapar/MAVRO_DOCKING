#!/usr/bin/env python3

import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2
import onnxruntime as ort

class YoloONNXNode(Node):
    def __init__(self):
        super().__init__('yolo_onnx_node')

        # Load ONNX model
        model_path = os.path.expanduser('~/yolo/yolov8n.pt')
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name

        self.img_size = 640  # expected input size
        self.conf_threshold = 0.3
        self.iou_threshold = 0.45

        self.subscription = self.create_subscription(
            Image,
            '/rover/camera/image_raw',
            self.listener_callback,
            10)

        self.publisher = self.create_publisher(
            Image,
            '/rover/camera/yolo/image_onnx',
            10)

        self.bridge = CvBridge()
        self.get_logger().info('YOLO ONNX Node started.')

    def preprocess(self, image):
        img = cv2.resize(image, (self.img_size, self.img_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))  # HWC to CHW
        img = np.expand_dims(img, axis=0)
        return img

    def postprocess(self, outputs, orig_img_shape):
        predictions = outputs[0][0]  # shape: (8400, 84)
        boxes = predictions[:, :4]
        scores = predictions[:, 4:5] * predictions[:, 5:]  # objectness * class scores
        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(scores.shape[0]), class_ids]

        # Filter by confidence
        mask = confidences > self.conf_threshold
        boxes = boxes[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # Rescale boxes to original image
        h, w = orig_img_shape[:2]
        scale_w, scale_h = w / self.img_size, h / self.img_size
        boxes[:, 0] *= scale_w
        boxes[:, 2] *= scale_w
        boxes[:, 1] *= scale_h
        boxes[:, 3] *= scale_h

        # Convert to xyxy
        boxes_xyxy = np.zeros_like(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2

        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes_xyxy.tolist(),
            scores=confidences.tolist(),
            score_threshold=self.conf_threshold,
            nms_threshold=self.iou_threshold
        )

        if len(indices) == 0:
            return []

        indices = indices.flatten()
        results = []
        for i in indices:
            box = boxes_xyxy[i].astype(int)
            results.append((box, confidences[i], class_ids[i]))

        return results

    def draw_detections(self, image, detections):
        for box, score, class_id in detections:
            x1, y1, x2, y2 = box
            label = f"{class_id}: {score:.2f}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return image

    def listener_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"CV Bridge error: {e}")
            return

        input_tensor = self.preprocess(cv_image)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        detections = self.postprocess(outputs, cv_image.shape)
        annotated_image = self.draw_detections(cv_image, detections)

        out_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloONNXNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

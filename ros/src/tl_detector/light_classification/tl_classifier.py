from styx_msgs.msg import TrafficLight
import tensorflow as tf
import numpy as np
import os
import rospy
from PIL import Image
import datetime


RUNNING_SIMULATOR = True
RUNNING_REAL_LIFE = not RUNNING_SIMULATOR

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        
        self.current_light = TrafficLight.UNKNOWN
        self.last_light = TrafficLight.UNKNOWN
        
        if RUNNING_SIMULATOR:
            graph_location = r'light_classification/SimModel/frozen_inference_graph.pb'
        if RUNNING_REAL_LIFE:
            graph_location = r'light_classification/RealImagesModel/frozen_inference_graph.pb'
        #print "Using graph file: {0}".format(graph_location)
        self.threshold = 0.20
        self.detection_graph = tf.Graph() 
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(graph_location, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        
        self.sess = tf.Session(graph=self.detection_graph)
        
        # The input placeholder for the image.
        # `get_tensor_by_name` returns the Tensor with the associated name in the Graph.
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')

        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.scores = self.detection_graph.get_tensor_by_name('detection_scores:0')

        # The classification of the object (integer id).
        self.classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0') 
        

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction
        
        with self.detection_graph.as_default():
            img_expand = np.expand_dims(image, axis=0)
            (scores, classes, num_detections) = self.sess.run(
                [self.scores, self.classes, self.num_detections],
                feed_dict={self.image_tensor: img_expand})

        scores = np.squeeze(scores)
        classes = np.squeeze(classes)
        num_detections = np.squeeze(num_detections)
        
        #print "Number of Detections: {0}".format(int(num_detections))
        #print "Most Confident Classification: {0} with score {1}".format(int(classes[0]), scores[0])
        #print "Next Most Confident Classification: {0} with score {1}".format(int(classes[1]), scores[1])    
        
        
        #The classifier has high confidence when detecting green lights, but it also has high confidence of
        #incorrectly classifying green lights.  So if the most confident classification is green, double check
        #by looking at the second most confident classification and see if the first was a fluke.
        if int(classes[0]) == 1:  #most confident classification is green
            if scores[0] > 2.5 * self.threshold:
                print "GREEN LIGHT"
                self.current_light = TrafficLight.GREEN
            
            elif int(num_detections) > 1:    
                if int(classes[1]) == 1:  #second most confident classification is green
                    if scores[1] > 1.5 * self.threshold:
                        print "GREEN LIGHT"
                        self.current_light = TrafficLight.GREEN
                if int(classes[1]) == 2: #second most confident classification is red
                    if scores [1] > self.threshold:
                        print "RED LIGHT"
                        self.current_light = TrafficLight.RED
                if int(classes[1]) == 3: #second most confident classification is red
                    if scores [1] > self.threshold:
                        print "YELLOW LIGHT"
                        self.current_light = TrafficLight.YELLOW
            else:
                self.current_light = TrafficLight.UNKNOWN
                    
        if int(classes[0]) == 2:  #most confident classification is red
            if scores [0] > self.threshold:
                print "RED LIGHT"
                self.current_light = TrafficLight.RED
            else:
                self.current_light = TrafficLight.UNKNOWN
        if int(classes[0]) == 3:  #most confident classification is yellow
            if scores [0] > self.threshold:
                print "YELLOW LIGHT"
                self.current_light = TrafficLight.YELLOW
            else:
                self.current_light = TrafficLight.UNKNOWN
        
        self.last_light = self.current_light
        
        return self.current_light
    
        
        
#!/usr/bin/env python

import rospy
import math
from sensor_msgs.msg import LaserScan
from race.msg import pid_input

# Some useful variable declarations.
angle_range = 240 # Hokuyo 4LX has 240 degrees FoV for scan
desired_distance = 0.8 # distance from the wall (in m). (defaults to right wall). You need to change this for the track
vel = 30 # this vel variable is not really used here.
delay = 0.1 # delay in seconds
forward_projection = vel * delay / 30 # distance (in m) that we project the car forward for correcting the error. You have to adjust this.
forward_projection = 1
error = 0.0 # initialize the error
car_length = 0.50 # Traxxas Rally is 20 inches or 0.5 meters. Useful variable.
theta = math.radians(70) # angle being swept (in degrees)

brake_dist = 1 # distance to start braking (m)
max_dist = 4
min_speed = 25

# Handle to the publisher that will publish on the error topic, messages of the type 'pid_input'
pub = rospy.Publisher('error', pid_input, queue_size=10)

def getRange(data,angle):
	# data: single message from topic /scan
	# angle: between -30 to 210 degrees, where 0 degrees is directly to the right, and 90 degrees is directly in front
	# Outputs length in meters to object with angle in lidar scan field of view
	# Make sure to take care of NaNs etc.
	angle -= math.pi/2
	index = (angle - data.angle_min) / data.angle_increment
	if math.isnan(data.ranges[int(index)]):
		return max_dist
	return data.ranges[int(index)]

def callback(data):
	a = getRange(data,theta) # obtain the ray distance for theta
	b = getRange(data,0) # obtain the ray distance for 0 degrees (i.e. directly to the right of the car)

	dist_ahead = getRange(data, math.radians(90))

	## Your code goes here to determine the projected error as per the alrorithm
	# Compute Alpha, AB, and CD..and finally the error.
	alpha = math.atan((a * math.cos(theta) - b) / (a * math.sin(theta)))
	ab = b * math.cos(alpha)
	ac = forward_projection
	cd = ab + ac * math.sin(alpha)
	error = desired_distance - cd

	msg = pid_input() # An empty msg is created of the type pid_input



	# this is the error that you want to send to the PID for steering correction.
	msg.pid_error = error
	msg.pid_vel = vel # velocity error can also be sent.


	# msg.pid_vel = vel - max_dist/(dist_ahead - brake_dist)
	# if msg.pid_vel < min_speed:
	# 	msg.pid_vel = min_speed
	# elif msg.pid_vel > vel:
	# 	msg.pid_vel = vel
	# msg.pid_vel = min_speed + (vel-min_speed) * (dist_ahead - brake_dist)/max_dist
	pub.publish(msg)

	print("alpha: %lf, dist_ahead: %lf" % (alpha, dist_ahead))

if __name__ == '__main__':
	print("Hokuyo LIDAR node started")
	
	theta = math.radians(float(raw_input("theta [70]: ") or "70"))
	desired_distance = float(raw_input("desired_distance [1]: ") or "1")
	vel = float(raw_input("velocity [40]: ") or "40")

	rospy.init_node('dist_finder',anonymous = True)
	# TODO: Make sure you are subscribing to the correct car_x/scan topic on your racecar
	rospy.Subscriber("/car_9/scan",LaserScan,callback)
	rospy.spin()


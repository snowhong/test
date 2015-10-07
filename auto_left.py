#!/usr/bin/env python
import rospy
import numpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
#from sonar import SonarArray 
INIT = 1
SAFE_FORWARD = 0.3
SAFE_LEFT = 0.5
SAFE_RIGHT= 0.5
LASER_RANGE = 360

def callback(sensor_data):
	if INIT == 1:
		init_max = max(sensor_data.ranges)
		global INIT
		print(len(sensor_data.ranges))
		INIT = 0
	base_data = Twist()
	forward_dis = sensor_data.ranges[LASER_RANGE/2]
	right_dis = numpy.min(sensor_data.ranges[0:LASER_RANGE/3])
	left_dis = numpy.min(sensor_data.ranges[LASER_RANGE-LASER_RANGE/3:LASER_RANGE])

	print ('left_distance:', left_dis )
	if forward_dis <= SAFE_FORWARD: #and left_dis > SAFE_LEFT and right_dis > SAFE_RIGHT:
		base_data.linear.x = 0
		if left_dis > SAFE_LEFT and right_dis > SAFE_RIGHT:
			#Just Give it a Direction(In this case we want robot keep the SAFE_LEFT value, that is to say, make the left side of robot keep a safe distance from the wall)
			base_data.angular.z = -0.3
			print ('right_distance:', right_dis )
	elif left_dis <= SAFE_LEFT:
		#Turn Right
		base_data.angular.z = -0.1
	elif left_dis >= SAFE_LEFT+0.2:
		base_data.angular.z = 0.1
	elif right_dis <= SAFE_RIGHT:
		#Turn Left
		base_data.angular.z = 0.1
##when a laser value change definately, it find a hole
#print left_dis
	else:
		base_data.linear.x = 0.2
	pub.publish(base_data)

if __name__ == '__main__':
	rospy.init_node('wall_mover')
	rospy.Subscriber('/p3dx/laser/scan', LaserScan, callback)
	pub = rospy.Publisher('cmd_vel', Twist, queue_size=100)
	rospy.spin()

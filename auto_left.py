#1.detect the signifacant change on the laser left value, judge that is the door or a cave
#2. change the strage when left_dir is over SAFE_LEFT
#
#
#!/usr/bin/env python
import rospy
import numpy
import time
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
#from sonar import SonarArray 
INIT = 1
SAFE_FORWARD = 0.3
SAFE_LEFT = 0.3
SAFE_RIGHT= 0.3
LASER_RANGE = 360
corner = 0
init_min = 999

def callback(sensor_data):
	base_data = Twist()
	forward_dis = numpy.min(sensor_data.ranges[LASER_RANGE/4:3*LASER_RANGE/4])
#right_dis = numpy.min(sensor_data.ranges[0:LASER_RANGE/3])
#left_dis = numpy.min(sensor_data.ranges[LASER_RANGE-LASER_RANGE/3:LASER_RANGE])
	right_dis = sensor_data.ranges[0]
	left_dis = sensor_data.ranges[LASER_RANGE-1]
	global corner
	global init_min 

	if INIT == 1:
		#Get The Closet Point and Go There!
		if(init_min > min(sensor_data.ranges)):
			init_min = min(sensor_data.ranges)
		global INIT
		print(len(sensor_data.ranges))
		print time.strftime("%H:%M:%S----"),forward_dis
		print 'init_min:',init_min
		if(init_min - 0.1 > forward_dis or forward_dis > init_min + 0.1 ):
			base_data.angular.z = -0.2
			time.sleep(0.1)
			pub.publish(base_data)
			return
		if(forward_dis > SAFE_FORWARD):
			print "tun right!"
			base_data.linear.x = -0.2
			time.sleep(0.1)
			pub.publish(base_data)
		INIT = 0
#print ('left_distance:', left_dis )

	if forward_dis <= SAFE_FORWARD:
		base_data.linear.x = 0
		if corner == 0 or corner == 1:
			if left_dis <= SAFE_LEFT:
				#Turn Right
				base_data.angular.z = -0.1
				corner =  1
				print "left safe!", corner
			if right_dis <= SAFE_RIGHT:
				#Turn Left
				base_data.angular.z = 0.1
				if corner == 1:
					corner =2
				print "right safe!",corner
		if corner == 2:
			if left_dis <= SAFE_LEFT and right_dis <= SAFE_RIGHT:
				print "avoid corner stuck!"
				if right>= left_dis:
					base_data.angular.z = -0.2
				else:
					base_data.angular.z = 0.2
				corner = 0

		if left_dis > SAFE_LEFT  and right_dis > SAFE_RIGHT:
		#Just Give it a Direction(In this case we want robot keep the SAFE_LEFT value, that is to say, make the left side of robot keep a safe distance from the wall)
			base_data.angular.z = -0.1
			print "clear corner value"
			corner = 0
			
	else:
		base_data.linear.x = 0.2

		if left_dis <= SAFE_LEFT:
			base_data.angular.z = -0.1
		elif right_dis <= SAFE_RIGHT:
			base_data.angular.z = 0.1
		if left_dis > SAFE_LEFT + 0.2:
			base_data.angular.z = 0.1

	pub.publish(base_data)

if __name__ == '__main__':
	rospy.init_node('wall_mover')
	rospy.Subscriber('/p3dx/laser/scan', LaserScan, callback)
	pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
	rospy.spin()

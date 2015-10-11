#1.detect the signifacant change on the laser left value, judge that is the door or a cave
#2. change the strage when left_dir is over SAFE_LEFT. Is safe flag ok?
#3. because it want keep left so it turn left from start
#
#!/usr/bin/env python
import rospy
import numpy
import time
import math
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
#from sonar import SonarArray 
INIT = 1
SAFE_DISTANCE = 0.5 #This is the safe window for the whole robot
SAFE_FORWARD = 0.5
SAFE_LEFT = 0.8
SAFE_RIGHT = 0.8
LASER_RANGE = 500
RIGHT_LASER_RANGE1 = 0
RIGHT_LASER_RANGE2 = LASER_RANGE/3
LEFT_LASER_RANGE1 = LASER_RANGE - LASER_RANGE/3
LEFT_LASER_RANGE2 = LASER_RANGE - 1
corner = 0
init_min = 999
PRE_LEFT_LASER = 0
LEFT_LIMIT = 1

def first_class(sensor_data):
	if(numpy.min(sensor_data.ranges) < SAFE_DISTANCE):
		move_data = Twist()
		move_data.angular.z = -0.2
		pub.publish(move_data)
		return False
	else:
	 	return True
	 

def init_robot(sensor_data):
	global INIT
	global init_min 
	if INIT == 1:
		direct_dis = numpy.min(sensor_data.ranges[(LASER_RANGE/2) - 5 :(LASER_RANGE/2) + 5])
		if(init_min > min(sensor_data.ranges)):
			init_min = min(sensor_data.ranges)
		print "Laser Data Range:",len(sensor_data.ranges)
		print time.strftime("%H:%M:%S----"),direct_dis
		print "init_min:", init_min
		if(init_min - 0.1 > direct_dis or direct_dis > init_min + 0.1 ):
			move_data = Twist()
			move_data.angular.z = -0.2
			time.sleep(0.1)
			pub.publish(move_data)
		else:
			print "FINISH INIT, FIND GOAL............"
			INIT = 0
			return True
		return False
	else:
	  return True
def filter_nan(sensor_data):
	filter_data= filter(lambda v: v==v, sensor_data)
	return filter_data

def callback(sensor_data):
	base_data = Twist()
	pre_forward_data= sensor_data.ranges[RIGHT_LASER_RANGE2:LEFT_LASER_RANGE1]
	forward_data = filter_nan(pre_forward_data)

#forward_data = forward_data[math.isnan(forward_data)]
	forward_dis = numpy.min(forward_data)
	print "front min dis(angular = 60):", forward_dis
#right_dis = numpy.min(sensor_data.ranges[0:LASER_RANGE/3])
#left_dis = numpy.min(sensor_data.ranges[LASER_RANGE-LASER_RANGE/3:LASER_RANGE])
	##FIXME:Only select one value test the rubustness.
	#right_dis = sensor_data.ranges[0]
	#left_dis = sensor_data.ranges[RIGHT_LASER_RANGE2]
	right_dis = numpy.mean(sensor_data.ranges[RIGHT_LASER_RANGE1:RIGHT_LASER_RANGE2])
	left_dis = numpy.mean(sensor_data.ranges[LEFT_LASER_RANGE1:LEFT_LASER_RANGE2])

	global corner
	global PRE_LEFT_LASER

	if_finish_init = init_robot(sensor_data)
	PRE_LEFT_LASER = left_dis

	if(if_finish_init):
		if(first_class(sensor_data)):
			if forward_dis <= SAFE_FORWARD:
				base_data.linear.x = 0
				if corner == 0 or corner == 1:
					if left_dis <= SAFE_LEFT:
						#Turn Right
						base_data.angular.z = -0.1
						corner =  1
		#print "left safe!", corner
					if right_dis <= SAFE_RIGHT:
						#Turn Left
						base_data.angular.z = 0.1
						if corner == 1:
							corner =2
		#print "right safe!",corner
				if corner == 2:
					if left_dis <= SAFE_LEFT and right_dis <= SAFE_RIGHT:
						print "avoid corner stuck!"
						##FIXME: Here may let robot get stuck at corner, turn left and then turn right.
						base_data.angular.z = -0.2
						corner = 0
		
				if left_dis > SAFE_LEFT  and right_dis > SAFE_RIGHT:
				#Just Give it a Direction(In this case we want robot keep the SAFE_LEFT value, that is to say, make the left side of robot keep a safe distance from the wall)
					base_data.angular.z = -0.1
		#print "clear corner value"
					corner = 0
					
			else:
				left_change = numpy.fabs(left_dis - PRE_LEFT_LASER)
				if(left_change > LEFT_LIMIT):
					if(left_dis > SAFE_LEFT and right_dis > SAFE_RIGHT):
						print 'left_change:',left_change
						base_data.linear.x = 0
						base_data.angular.z = 0.2
						pub.publish(base_data)
						return
						base_data.linear.x = 0.2
		
				else:	
					base_data.linear.x = 0.2
		
					if left_dis <= SAFE_LEFT:
						base_data.angular.z = -0.1
					elif right_dis <= SAFE_RIGHT:
						base_data.angular.z = 0.1
					if left_dis > SAFE_LEFT + 0.2:
						base_data.angular.z = 0.1
		
			PRE_LEFT_LASER = left_dis
			pub.publish(base_data)

if __name__ == '__main__':
	rospy.init_node('wall_mover')
	rospy.Subscriber('/base_scan', LaserScan, callback)
	pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
	rospy.spin()

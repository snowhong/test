#-------------- Imports -------------#

from geometry_msgs.msg import Pose, PoseArray, Quaternion
from pf_base import PFLocaliserBase
import math
import numpy.ma as ma
import rospy
from util import rotateQuaternion, getHeading
import random
from time import time
import datetime
import math
#from __future__import print_function


#-------------- PFLocaliser Class Methods-------------#

class PFLocaliser(PFLocaliserBase):

    #constructor
    def __init__(self):

        #Call the superclass constructor
        super(PFLocaliser, self).__init__()

        #Set motion model parameters
        self.ODOM_ROTATION_NOISE = 0.05
        self.ODOM_TRANSLATION_NOISE = 0.014
        self.ODOM_DRIFT_NOISE = 0.006

        #Sensor model readings
        self.NUMBER_PREDICTED_READINGS = 100

    def initialise_particle_cloud(self, initialpose):
        #Set particle cloud to initialpose plus noise
        noise = 1
        #create an array of Poses
        posArray = PoseArray()

        #iterate over the number of particles and append to PosArray
        for x in range(0, self.NUMBER_PREDICTED_READINGS): 
            pose = Pose()

            pose.position.x =  random.gauss(initialpose.pose.pose.position.x, noise)
            pose.position.y = random.gauss(initialpose.pose.pose.position.y, noise)
            pose.position.z = 0

        #TODO:reconfig the parameters
            pose.orientation = rotateQuaternion(initialpose.pose.pose.orientation, math.radians(random.gauss(0,30)))

            posArray.poses.extend([pose])

        #print posArray
        return posArray

    def update_particle_cloud(self, scan):

        ##---------------------------##
    ##---------PARAMETERs--------##
    ##---------------------------##
        #list of poses
        sum_weights = 0
        sum_count = 0
        cumulate_weight= [] 
        separate_weight= []

        cloud_pose = self.particlecloud.poses

    ##---------------------------##
    ##-----------WEIGHT----------##
    ##---------------------------##

    ##remove the invalid value.
        scan.ranges=ma.masked_invalid(scan.ranges).filled(scan.range_max)

    ##record the weight for each pose, in case to use it again
        pairs_partweight=[]
    #time1 = datetime.datetime.now() 

    ##weight need scan_data and current_pose
        for i in cloud_pose:
            particle_weight = self.sensor_model.get_weight(scan, i)
            sum_weights+= particle_weight
            pairs_partweight.append([i,particle_weight])
    #time2 = datetime.datetime.now()
    ##calculate the time consume
    #print (time2 - time1 ).microseconds

        for pair in pairs_partweight:
            particle_weight = pair[1]
            weight_over_sum = particle_weight/sum_weights
            sum_count+= weight_over_sum
            cumulate_weight.extend([sum_count])    

    #print cumulate_weight
    ##-----------------------##
    ##---------UPDATE--------##
    ##-----------------------##
        updated_particlecloud = PoseArray()
        for particle in cloud_pose:
            count = 0
            rand = random.uniform(0,1)
            for i in cumulate_weight:
                ##TODO:the repeat pose doesn't matters
                if rand <= i:
                    updated_particlecloud.poses.extend([cloud_pose[count]])
                    #print count
                    break
                count=count+1

    ##-----------------------##
    ##---------NOISE---------##
    ##-----------------------##

        updated_with_noise_cloud = PoseArray()

        for i in updated_particlecloud.poses:
            noise_pose = Pose()
            noise_pose.position.x = random.gauss(i.position.x,(i.position.x * self.ODOM_DRIFT_NOISE))
            noise_pose.position.y = random.gauss(i.position.y,(i.position.y * self.ODOM_TRANSLATION_NOISE))
            noise_pose.orientation = rotateQuaternion(i.orientation, math.radians(random.uniform(-self.ODOM_ROTATION_NOISE,self.ODOM_ROTATION_NOISE)))

            updated_with_noise_cloud.poses.extend([noise_pose])

    ##-----------------------##
    ##---------OUTPUT--------##
    ##-----------------------##

        self.particlecloud = updated_with_noise_cloud


    def estimate_pose(self):
        'Method to estimate the pose'

        '''Create new estimated pose, given particle cloud
        E.g. just average the location and orientation values of each of
        the particles and return this.
        Better approximations could be made by doing some simple clustering,
        e.g. taking the average location of half the particles after 
        throwing away any which are outlier'''


        #declare some variables 
        x,y,z,orix,oriy,oriz,oriw,count = 0,0,0,0,0,0,0,0

        #iterate over each particle extracting the relevant
        #averages

        normalise_pose = [] 
        for particle in self.particlecloud.poses:
            x += particle.position.x
            y += particle.position.y
            z += particle.position.z
            orix += particle.orientation.x
            oriy += particle.orientation.y
            oriz += particle.orientation.z
            oriw += particle.orientation.w
            
            #normalise_pose.extend([particle])
            normalise_pose.append(particle)



        count = len(self.particlecloud.poses)

        #create a new pose with the averages of the location and 
        #orientation values of the particles
        pose = Pose()

        pose.position.x = x/count
        pose.position.y = y/count
        pose.position.z = z/count

        pose.orientation.x = orix/count
        pose.orientation.y = oriy/count
        pose.orientation.z = oriz/count
        pose.orientation.w = oriw/count

        ##
        sum_x = 0
        sum_y = 0
        sum_w = 0
        for particle in self.particlecloud.poses:
            sum_x = sum_x + pow(particle.position.x - pose.position.x, 2)
            sum_y = sum_y + pow(particle.position.y - pose.position.y, 2)
            sum_w = sum_w + pow(particle.orientation.w - pose.orientation.w, 2)

        standard_dev_x=math.sqrt(sum_x/count)
        standard_dev_y=math.sqrt(sum_y/count)
        standard_dev_w=math.sqrt(sum_w/count)
        print standard_dev_x, standard_dev_y, standard_dev_w

        print self.pre_st_x , self.pre_st_y , self.pre_st_w 
        print self.pre_st_x - float(standard_dev_x), self.pre_st_y - float(standard_dev_y), self.pre_st_w - float(standard_dev_w)

        self.pre_st_x=standard_dev_x
        self.pre_st_y=standard_dev_y
        self.pre_st_w=standard_dev_w

        print pose.position.x - self._pre_pose.position.x
        if (pose.position.x - self._pre_pose.position.x) > 0.2:
            with open("./pose.txt","a+") as myfile:
                #now = rospy.get_rostime()
                time = datetime.datetime.now() 
                myfile.write("**********************time:")
                #myfile.write(str(now.secs)+"."+str(now.nsecs)+"\n")
                myfile.write(str(time)+"\n")
    
                myfile.write(str(pose)+"\n")
                myfile.close()

        self._pre_pose = pose
        return pose

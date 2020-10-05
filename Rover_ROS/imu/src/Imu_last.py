#! /usr/bin/env python
import rospy
import numpy as np
from sensor_msgs.msg import Imu, MagneticField, JointState
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from nav_msgs.msg import Odometry

imu_node = Imu()

class ubication(object):
        def __init__(self):
                self.pub = rospy.Publisher('/yaw', Imu, queue_size=10)

		#self.cuenta = 0

		self.xmax = 0
		self.ymax = 0
		self.xmin = 0
		self.ymin = 0

                self.x = 0
                self.y = 0
                self.z = 0
                self.yaw = 0
		self.yaw_1 = 0
		self.count = 0

		self.mag_yaw = 0

		#VARIABLE RORATION MATRIX
		self.acc_x = 0
		self.acc_y = 0
		self.acc = np.zeros([2,1])
		self.w = 0
		self.RB = np.zeros([2,2])
		self.RB_ = np.zeros([2,1])

		#VARIABLES FILTER IMU_ACC
		self.accx = 0.0
		self.accy = 0.0
		self.acc_x_1 = 0.0
		self.acc_y_1 = 0.0

                rospy.Subscriber('/imu/mag', MagneticField, self.mag)
		rospy.Subscriber('/imu/data', Imu, self.imu)
		rospy.Subscriber('/main_node', JointState, self.calibration)

        def mag(self, data):
		x = data.magnetic_field.x
		y = data.magnetic_field.y
		z = data.magnetic_field.z

		if x>self.xmax: self.xmax = x
		if y>self.ymax: self.ymax = y

		if x<self.xmin: self.xmin = x
		if y<self.ymin: self.ymin = y

		xsf = (self.ymax - self.ymin)/(self.xmax -self.xmin)
		ysf = (self.xmax - self.xmin)/(self.ymax - self.ymin)

		xoff = ((self.xmax - self.xmin)/2 - self.xmax)*xsf
		yoff = ((self.ymax - self.ymin)/2 - self.ymax)*ysf

		self.x = xsf*x + xoff
		self.y = ysf*y + yoff

		self.mag_yaw = np.arctan2(-self.y,self.x)

		#if self.cuenta == 0:
		#	self.yaw_1 = np.arctan2(-y, x)
		#	self.cuenta = self.cuenta + 1

		#if self.calibration == ['Termino']:
		#	self.yaw_1 = np.arctan2(-self.y, self.x)
		#	self.calibration = []
		#	print self.yaw_1

	def calibration(self, data):
		self.calibration = data.name
		if self.calibration == ['Termino']:
			self.yaw_1 = np.arctan2(-self.y, self.x)
			#self.calibration = []
			print self.yaw_1*180/np.pi

        def imu(self, data):
                orientation_q = data.orientation
		orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
                euler = euler_from_quaternion(orientation_list)
                #self.yaw = (euler[2] + self.yaw_1)*(180/np.pi)
                self.yaw = euler[2]

		#FILTER FOR ACCELEROMETERS
		self.accx = data.linear_acceleration.x
		self.accy = data.linear_acceleration.y

		self.acc_x = 0.0155*self.accx + 0.0155*self.acc_x_1 + 0.9691*self.acc_x
		self.acc_y = 0.0155*self.accy + 0.0155*self.acc_y_1 + 0.9691*self.acc_y

		#ROTATION MATRIX
		self.acc = np.array([ [self.acc_x - 0.004],[self.acc_y - 0.014] ])
		self.w = data.angular_velocity.z - 0.02

		self.RB = np.array([ [np.cos(self.yaw), -np.sin(self.yaw)],
                                        [np.sin(self.yaw), np.cos(self.yaw)]  ])

		self.RB_ = np.dot(self.RB, self.acc)

		#UPDATE VARIABLES
		self.acc_x_1 = self.accx
		self.acc_y_1 = self.accy


	def main(self):
		rate = rospy.Rate(20)
		while not rospy.is_shutdown():

			imu_node.header.frame_id = "NODE IMU ROTATE"
			imu_node.header.stamp = rospy.get_rostime()

			imu_node.orientation.x = self.yaw
			imu_node.orientation.y = self.mag_yaw
			imu_node.angular_velocity.z = self.w
			imu_node.linear_acceleration.x = self.RB_[0,0]
			imu_node.linear_acceleration.y = self.RB_[1,0]

			self.pub.publish(imu_node)
			rate.sleep()


if __name__=='__main__':
        try:
                rospy.init_node('Orientation',anonymous=True, disable_signals=True)
                print "Nodo YAW Creado"
                cv = ubication()
		cv.main()

        except rospy.ROSInterruptException:
                pass

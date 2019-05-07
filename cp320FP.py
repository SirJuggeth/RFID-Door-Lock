# By Tim, Justin, Ryan

#the next three imports bellow are for the RFID
import RPi.GPIO as GPIO
from datetime import datetime
import time
#the next three imports are for the oled(as well as time)
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
#for the ir
import spidev
channel=1
spi=spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz = 5000
#set gpio mode
GPIO.setmode(GPIO.BCM)
ENABLE_PIN=18
#This could presumeably be modified for other serial devices
PORT_RATE=2400
BYTESIZE=8
PARITY="N"
STOP_BITS=1
END_LINE='\n'
# any GPIO pin can be used
SERIAL_PIN=27
START_LEVEL=False
STOP_LEVEL=True
HALF_BIT_TIME=1/float((2*PORT_RATE))
THREE_HALF_BIT_TIME=3*HALF_BIT_TIME
ONE_BIT_TIME=2*HALF_BIT_TIME
HALF_BIT_TIME_US=int(HALF_BIT_TIME*1000000)
THREE_HALF_BIT_TIME_US=int(1000000*THREE_HALF_BIT_TIME)
ONE_BIT_TIME_US=int(1000000*ONE_BIT_TIME)
#in seconds
ALLOWABLE_DEAD_TIME=1
CHAR_TIME_US=(BYTESIZE*2+STOP_BITS)*HALF_BIT_TIME_US
message=[]
chartimes=[]
#In order to be fast enough in Python, this routine just generates an array
# of transition times on the serial pin (in microseconds)
# At the beginning of each new character, the time is reset to zero
# (Number of transitions for a character must be odd)
##
def timeChar():

	timestart=0
	times=[]

# wait for start bit
	input_value=GPIO.input(SERIAL_PIN)
	while input_value != START_LEVEL:
		input_value=GPIO.input(SERIAL_PIN)
# get data  transition time of start bit

	dt=datetime.now()
	nowus=dt.microsecond
	times.append(nowus)
	timestart=nowus
#calculate time for the entire character
	timeend=timestart+CHAR_TIME_US

# get data  transition time of other bits
# stop when the time for the entire character has passed
	while nowus<timeend:

		oldLevel=input_value
		input_value=GPIO.input(SERIAL_PIN)

		while input_value == oldLevel:
			input_value=GPIO.input(SERIAL_PIN)

		dt=datetime.now()
		nowus=dt.microsecond
		times.append(nowus)

	times.append(times[0])

# wait for stop bit

	input_value=GPIO.input(SERIAL_PIN)
	while input_value != STOP_LEVEL:
		input_value=GPIO.input(SERIAL_PIN)

#now make times relative to the start of the character
#so the start bit is at 0, by definition

	temptime=times[0]

	for i in range(len(times)):
		times[i]=times[i]-temptime

	return times
# given an array of transition times, and knowing the time for a bit,
# and that the character starts with a START bit, the complete
# bit string can be generated
# The data comes in LSB first, so it gets reversed at the end
##
def convertChar(thesetimes):
	bytestr=''
	curtime=0
	curLevel='1'
	altLevel='0'
	curBit=0
	if thesetimes[1]<CHAR_TIME_US:

		for i in range(len(times)):
			while thesetimes[i]>curtime+THREE_HALF_BIT_TIME_US:
				bytestr+=curLevel
				curtime+=ONE_BIT_TIME_US
				curBit+=1
			tempLevel=curLevel
			curLevel=altLevel
			altLevel=tempLevel

	return bytestr[::-1]

def lock():
	#set lock image
	# Load image based on OLED display height.  Note that image is converted to 1 bit color.
	image = Image.open('lockedimage_oled.png').convert('1')#change to lock image
	# Display image.
	disp.image(image)
	disp.display()
	#end display image

	#lock door with motor
	stepper_sequence=[]
	stepper_sequence.append([GPIO.HIGH, GPIO.LOW, GPIO.LOW,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.HIGH, GPIO.LOW,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.HIGH,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.LOW,GPIO.HIGH])

	stepsNeeded=128
	stepsTaken=0
	#stepsToZero=512-(stepsNeeded%512)
	#print("start of loop")
	#print(stepsNeeded)
	while stepsNeeded>stepsTaken:
		for row in reversed (stepper_sequence):
		#for row in stepper_sequence:
			GPIO.output(stepper_pins,row)
			time.sleep(0.01)
		stepsTaken+=1
	return
def unlock():
	# Load image based on OLED display height.  Note that image is converted to 1 bit color.
	image = Image.open('unlockedimage_oled.png').convert('1')
	# Display image.
	disp.image(image)
	disp.display()
	#end display image

	#move motor
	#print("")#needed to run code DO NOT REMOVE
	GPIO.setmode(GPIO.BCM)
	stepper_pins=[13,16,26,21]

	GPIO.setup(stepper_pins,GPIO.OUT)

	stepper_sequence=[]
	stepper_sequence.append([GPIO.HIGH, GPIO.LOW, GPIO.LOW,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.HIGH, GPIO.LOW,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.HIGH,GPIO.LOW])
	stepper_sequence.append([GPIO.LOW, GPIO.LOW, GPIO.LOW,GPIO.HIGH])

	stepsNeeded=128
	stepsTaken=0
	#stepsToZero=512-(stepsNeeded%512)
	#print("start of loop")
	#print(stepsNeeded)
	while stepsNeeded>stepsTaken:
		#for row in reversed (stepper_sequence):
		for row in stepper_sequence:
			GPIO.output(stepper_pins,row)
			time.sleep(0.01)
		stepsTaken+=1
	return
def rfid():
	try:
		charSpace=0
		msgIndex=1
		startTime=datetime.now()
		msgTime=startTime-startTime
		msgStarted=False
		msgDone=False

	#A message will be assumed to be complete if there
	# hasn't been a transition in ALLOWABLE_DEAD_TIME (seconds)
	#Processing of transisiton times isn't done until AFTER
	# the message is complete to allow a higher baud rate
		while not msgDone:
	#wait for activity
			input_value=GPIO.input(SERIAL_PIN)
			if input_value == STOP_LEVEL:
				thisTime=datetime.now()
				if not msgStarted:
					startTime=thisTime
				msgTime=thisTime-startTime
				if msgTime.seconds>ALLOWABLE_DEAD_TIME:
					msgDone=True
			else:
	# get a character
				chartimes=timeChar()
				startTime=datetime.now()
				msgStarted=True
				message.append(chartimes)
				msgIndex+=1
				#message is done, so disable reader
				#GPIO.output(ENABLE_PIN,GPIO.HIGH)
	return
def checkdoor():
	#time.sleep(2)
	data_scale=0
	while data_scale<2:
		adc=spi.xfer2([1,(8+channel)<<4,0])
		data=((adc[1]&3)<<8) +adc[2]
		data_scale=(data*3.3)/float(1023)
		data_scale=round(data_scale,2)
		#print (data_scale)
	return

####################Main Code ##################


#beginning of RFID main code

#The reader has an ENABLE pin, which must be LOW to read
GPIO.setup(ENABLE_PIN,GPIO.OUT)
GPIO.setup(SERIAL_PIN,GPIO.IN)
#This just makes a flash of the LED
GPIO.output(ENABLE_PIN,GPIO.HIGH)
time.sleep(0.5)
GPIO.output(ENABLE_PIN,GPIO.LOW)
# Initialize library.
disp.begin()
# Clear display.
disp.clear()
disp.display()
running=True
password='123'

#main program loop tracking status of peripherals
while running:
	rfid()#run the code to read from the RFID
	unlock()#run the code to unlock the door
	checkdoor()#run the code to check to see if the door has been closed
	lock()#run the code to lock the door
	except KeyboardInterrupt:
		x=input("please enter passoword to shutdown")
		if(x==password):
			running=False
		pass



#end program
GPIO.cleanup()

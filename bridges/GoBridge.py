###########################################################
#Multegula - GoBridge.py                                  #
#Functions to create local socket and messages            #
#Armin Mahmoudi, Daniel Santoro, Garrett Miller, Lunwen He#
###########################################################

#######IMPORTS#######
import socket #Needed for network communications
import time #Needed for labeling date/time
import datetime #Needed for labeling date/time
import queue #Needed for receive queue
#####################

########PARAMETERS########
BUFFER_SIZE = 200 #Arbitrary buffer size for received messages
DELIMITER = '##'
PAYLOAD_DELIMITER = '|'
LOCALHOST_IP = 'localhost'
DEFAULT_SRC = 'UNSET'
MULTICAST_DEST = 'EVERYBODY'
MULTEGULA_DEST = 'MULTEGULA'
TCP_PORT = 44444
##########################

class PyMessage :
	kind = ''
	src = ''
	dest = ''
	content = None
	multicast = False

	def crack(self, received):
		receivedArray = received.split(DELIMITER)
		self.src = receivedArray[0]
		self.dest = receivedArray[1]
		self.content = receivedArray[2].split(PAYLOAD_DELIMITER)
		self.kind = receivedArray[3].replace('\n', '')

	def assemble(self):
		return self.src + DELIMITER + self.dest + DELIMITER + self.content + DELIMITER + self.kind + '\n'

	def printMessage(self):
		print('source: ' + self.src + ', type: ' + self.kind + ', content: ' + str(self.content))

# GoBridge class
class GoBridge :
    ### __init___ - initialize and return GoBridge
    ## # this function starts the GoBridge running
	## # Returns a connected socket object GoBridge
	def __init__(self, src = DEFAULT_SRC) :
		# set the self src
		self.src = src;
		
		#Set up the connection
		GoSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		#Disable Nagle's Algorithm to decrease latency.
		#TCP_NODELAY sends packets immediately.
		GoSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		#Disable blocking so our receive thread can continue.
		#Currently blocking - I think this is okay. -Garrett
		#GoSocket.setblocking(0)
		
		try:
			#Try to open connection to local Go Bridge
			GoSocket.connect((LOCALHOST_IP, TCP_PORT))
		except:
			#NOTE: this is mostly useful for debugging, but in reality the game couldn't run without this.
			print(self.getPrettyTime() + " Can't connect. Is PyBridge up?")

		#And declare GoBridge
		self.GoSocket = GoSocket

		#Establish a queue for received messages
		self.receiveQueue = queue.Queue()

	## Get Pretty Time
	## # Get pretty time for printing in error logs.
	def getPrettyTime(self): 
		#Get Time
		timestamp = int(time.time())
		prettytime = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
		return 	'[' + prettytime + ']'
			
	## Build and Send Message
	## # this function builds and sends a message.
	## # Explicit encoding declaration became necessary in Python 3.
	def sendMessage(self, pyMessage):
		if pyMessage.src == DEFAULT_SRC:
			print('GoBridge: ' + self.getPrettyTime() + ' Source name not set. Cannot send message.')
		else:
			# determine if this is a multicast message
			if(pyMessage.multicast == True):
				pyMessage.dest = MULTICAST_DEST
			else:
				pyMessage.dest = MULTEGULA_DEST	

			# assemble the string version of the message
			toSend = pyMessage.assemble()

			try:	
				self.GoSocket.send(toSend.encode(encoding='utf-8'))
			except: 
				print('GoBridge: ' + self.getPrettyTime() + ' Error sending on GoSocket:')
				print('   ' + toSend);

	## Receive Thread
	## # this function receives a message from the receive buffer
	## # and adds it to a receive queue for pickup by other functions.
	def receiveThread(self):
		while True:
			receivedData = self.GoSocket.recv(BUFFER_SIZE)
			if not receivedData:
				pass
			else:
				self.receiveQueue.put(receivedData)

	## Receive Message
	## # this function pulls a message from the receive queue
	def receiveMessage(self):
		message = PyMessage()
		# only try and get a message if there is something in the queue.
		if not(self.receiveQueue.empty()):
			try:
				received = self.receiveQueue.get(block = False)
				message.crack(received)
			except:
				pass

		return message


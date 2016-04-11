#!/usr/bin/python
#Author : Brendan Lilly
#Filename: server.py
#Purpose : Accept commands from connected clients perform them.


#Imports
import sys
import socket  
import time 
import os
from threading import Thread

#Default values , PORT can change via command line
IPADDR = "127.0.0.1"
PORT= 50098
buffer = 4096
threadCount = 0
#Default end of transmission string for server messages
endOfTrans = "!@#"


#Checks if the command line arguments are in the correct range
if len(sys.argv) > 2:
	#If there are more than 2 arguments print usage clause
    print "Usage: " , sys.argv[0] , " [port]"
    exit(-1)
elif len(sys.argv)==2:
	try:
		#Cast the second cmd line arg as the port
		PORT = int(sys.argv[1])
	#If this raises and exception a type other than int was passed	
	except ValueError as error:
		print error 
		exit(-1)

# Name: processLife
# Description: all of the functionality for each client connection takes place here
# Parameters: cliSocket - the client socket descriptor
			# cliAddress- the clients address and port number touple
# Return : Void				
def processLife(cliSocket,cliAddress):
	#Successful connection has taken place
	clientAddress=cliAddress
	#Send the client the success message
	cliSocket.send("Server Message: HELLO\n")
	#Loop to wait for input from the client
	while True:
		#Start receiving data
		(cliData , cliAddress)= cliSocket.recvfrom(buffer)
		
		#Dir Command Start
		if(cliData.upper() == "DIR"):
			#If the client sends the DIR command
			try:
				#Call the listdir function on the current directory
				dirList = os.listdir(".")
				#Create a message to send back to the client
				message= "Current Directory Contents:\n"
				#Loop through the contents of the dirList array and append them to the message
				for listing in dirList:
					message = message + listing + "\n"
				#After all of the listings are in the string append the end of transmission string
				message = message + endOfTrans
				#Send the message to the client 
				cliSocket.send(message)
			#If an Exception is thrown while calling the listdir call 	
			except OSError as error:
				#Send the error back to the client with the end of transmission string appended to it
				cliSocket.send(str(error)+endOfTrans)
		#Dir Command End

		#CD command start
		elif(cliData.split(" ")[0].upper() == "CD"):
			#If the client sends the CD command
			#Keep track of the original directory
			originalDir = os.getcwd()
			try:
				#Attempt to change the directory to the second index of the string passed
				os.chdir(cliData.split()[1])
				#If successful send a success message back to the client 
				cliSocket.send("CD successful , the current working directory is:\n"+os.getcwd()+endOfTrans)
			except IndexError as iError:
				#If there is no second index passed with the CD command 
				#Send a missing argument message back to the client and change back to original dir
				cliSocket.send("Missing argument to the CD command. "+endOfTrans)
				os.chdir(originalDir)
			except OSError as error:
				#If client does not have the correct permissions
				#Send the error message back to the client and change back to the original dir
				cliSocket.send(str(error)+endOfTrans)
				os.chdir(originalDir)
		#CD command End
		
		#Download command start
		elif(cliData.split(" ")[0].upper() == "DOWNLOAD"):
			#If the client sends the download command 
			try:
				#Checks if the absolute passed or file name passed is valid
				if os.path.isfile(cliData.split(" ")[1]):
					
					fileName=cliData.split(" ")[1]
					#Attempt to open the file name passed
					try:
						file = open(fileName)
						#If successful send the "READY" message to the client
						cliSocket.send("READY\n"+endOfTrans)
						#Receive the response from the client as whether 
						# to send the files data or STOP
						(cliData , cliAddress)= cliSocket.recvfrom(buffer)
						#If the client sends back "READY"
						if cliData.upper() == "READY":
							#Send the file line by line
							for line in file:
								#print line 
								cliSocket.send(line)
							#Once the whole file is sent , send the end of transmission string
							cliSocket.send(endOfTrans)						
						else:
							#If the client responds with STOP then just send the end of transmission string
							cliSocket.send(endOfTrans)
					#If an exception is raised when opening the file		
					except IOError as error:
						#The user most likely does not have permissions to download 
						#The file
						cliSocket.send(str(error)+endOfTrans)
				else:
					#Send a file not found error back to the client
					cliSocket.send("FILE NOT FOUND\n"+endOfTrans)
			#If the IndexError exception is raised then there was a missing arg to the download command
			except IndexError as iError:
				#Send back the error to the client	
				cliSocket.send("Missing argument to the DOWNLOAD command. "+endOfTrans)
		
		#Download command end

		#Help command start
		elif(cliData.upper()=="HELP"):
			cliSocket.send("The available commands are:\n * DIR : Directory listing in the server.\n * CD <Directory> : Change directory on server.\n * DOWNLOAD <File Name>: Downloads the file from the server to the client.\n "+endOfTrans)
		#Help command end
		
		#BYE command start
		elif(cliData.upper()=="BYE"):
			#If the BYE command is received print the termination message to the log
			print("Connection to " + str(clientAddress) +" has been terminated.")
			#Close the clients socket descriptor and exit the process
			cliSocket.close()
			exit(0)
		#BYE command end

		#All other cases are bad input
		else:
			cliSocket.send("Unrecognised command type \"HELP\" for list of options "+endOfTrans)

			
#Create a socket for the upcoming connection
try:
	sockfd = socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
except socket.error as error:
    print error
    exit(-1)

#Bind the socket to the Ip address and port specified above
try:
	sockfd.bind(("",PORT))
except socket.error as error:
	print error 
	exit(-1)

	
#Listen for a connection
try:
	sockfd.listen(20)
except socket.error as error:
	print error 
	exit(-1)

#Loop to wait for data from client 	
child_pids = []
while True:
	#Attempt to receive data up until the buffer size set above
	try:
		
		cliSocket, cliAddress = sockfd.accept()
		print("Connected to client socket:"+ str(cliSocket) + " and client address: " + str(cliAddress))
		newpid= os.fork()
		if newpid == 0:
			processLife(cliSocket,cliAddress)
			#Add the pid to the array
			child_pids.append(newpid)
			#Call exit so the new child process will end
			os._exit(0)
		elif newpid < 0:
			sys.stderr.write("Failed to create the child process")
	except KeyboardInterrupt:
		#If the ^C keys are pressed gracefully end the server and quit
		print "\nThe server has been stopped\n"
		for x in  range(len(child_pids)):
			#Calls wait for each pid stored in the array
			os.waitpid(child_pids[x],0)
		exit(0)
	except socket.error as error:
		print error
		exit(-1)





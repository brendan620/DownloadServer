#!/usr/bin/python
#Author : Brendan Lilly
#Filename: client.py
#Purpose : Connect to the connection oriented concurrent download server.

#Imports
import sys
import socket  
import errno
import os

#Default port if none are passed in via cmd line arguments 
port = 50098
#Default end of transmission string for server messages
endOfTrans = "!@#"
#Default buffer size
buffer = 600 
#Checks if the command line arguments are in the correct range
if len(sys.argv) < 2 or len(sys.argv) > 3:
    print "Usage: " , sys.argv[0] , " <hostname> [port]"
    exit(-1)
elif len(sys.argv) == 2:
	#If there are 2 cmd line arguments just get the hostname
    hostname = sys.argv[1]
    try:
	#Converts the passed hostname to an ip address and assignes it
        ipAddr=socket.gethostbyname(hostname)
    except:
        print "Invalid hostname"
        exit(-1)
else:
    #If there are 3 command line arguments get the hostname and port number 
    hostname = sys.argv[1]
    port = int(sys.argv[2])
    try:
        ipAddr=socket.gethostbyname(hostname)
    except socket.error as error:
        print error
        exit(-1)

#Create a socket for the upcoming connection
try:
	sockfd = socket.socket(socket.AF_INET ,socket.SOCK_STREAM)
except socket.error as error:
	print error
	exit(-1)

#Try to connect to the ip address and port specified on the newly created socket
try:   
    sockfd.connect((ipAddr,port))
except socket.error as error:
    print error
    exit(-1)

#Receive the HELLO message from the server and print
successMsg = sockfd.recv(300)
print successMsg

#Find the home directory the client is running in
#this is where files will be downloaded to.
homeDir = os.getcwd()
fileData = ""

#Now that the client is connected loop for user input
while True:
		
		#Attempt to get input , exception will occur on ^C 
		try:
			#Loop to get valid input from user
			while True:
				#Prompt/command input
				message = raw_input("Enter command here: ")
				#If raw_input is the empty string or '' , message will evaluate to false and loop
				if message:
					#If message has some content send it to the server and break from the loop
					sockfd.sendto(message,(ipAddr,port))
					break
				
			#Download Command Start
			#Checks if the first term of the sent message was the 
			# key word for the download command
			if message.split(" ")[0].upper() == "DOWNLOAD":
				#Get the name of the file attempting to be downloaded
				fileName = message.split(" ")[1]
				#If it contains a '/' or absolute path
				if '/' in fileName:
					#Use the basename call to strip the path out 
					# just leaving the filename 
					fileName = os.path.basename(fileName)
				
				while True:
					#Receive the response from the server
					servData = sockfd.recv(buffer)
					#Check that the full message was received 
					if endOfTrans in servData:
						#If the full message was received trim the end of transmission string
						servData=servData.split(endOfTrans)[0]
						#Print the servers response to the clients screen
						print servData
						#If the server responded with "READY\n" then the file exists
						if servData == "READY\n":
								#Loop to get valid input from user
								while True:
									#Prompt/command input
									message = raw_input("Enter READY: to confirm download or STOP: to stop the download from taking place\n")
									#If raw_input is the empty string or '' , message will evaluate to false and loop
									if message:
										#Check that the message is one of the two valid commands
										if message.upper()=="READY" or message.upper()=="STOP":
											#Send the valid message to the server and break from the input loop
											sockfd.sendto(message,(ipAddr,port))
											break
										else:
											#Error message to user and loop for valid input
											print("Invalid Input. \n")
								
								#Start attempting to receive the file 			
								servData = sockfd.recv(buffer)
								#If the response from the server is not just the end of transmission string
								#then the user chose to download the file
								if servData != endOfTrans:
									#While the end of transmission string is not found 
									while endOfTrans not in servData:
										#Append the servers data to the fileData
										fileData = fileData + servData
										servData = sockfd.recv(buffer)
									#Append the final server data to the fileData string
									fileData = fileData + servData	
									#Trim off the the end of transmission string
									fileData = fileData[:-3]
									#Attempt to write the data to a new file
									try:
										#Call open and pass it the home directory found above 
										# concatenated with the file name and open it with write permissions										
										with open(os.path.join(homeDir,fileName),'w') as newFile:
											#Write the fileData to this new file
											newFile.write(fileData)
										#If this occurs without exception print the success message to the client's screen	
										print("File Downloaded Successfully and can be found in " + str(os.path.join(homeDir,fileName)))
									except OSError as error:
										#If an OSError occurs print it to the client
										print error 
						#Break from loop when the end of transmission string is recieved 
						break
			#Download command end

			#All other I/O with the server start
			else:					
				#Loop for data from the server
				while True:
					#Receive data from server
					servData = sockfd.recv(buffer)
					#Checks that the end of transmission string is found
					if endOfTrans in servData:
						#Trim the string from the received data
						servData=servData.split(endOfTrans)[0]
						#Print the servData to the clients screen and break from the loop
						print servData
						break
			#All other I/O with the server end		
		
		#Exception for keyboard interrupt from the user 
		except KeyboardInterrupt:
			#If the ^C keys are pressed gracefully end the client and quit
			#Send the "BYE" command to the server
			sockfd.sendto("BYE",(ipAddr,port))
			#Close socket and exit
			sockfd.close()
			exit(0)		

#Close the Socket connection 
sockfd.close()

import socket

julius_host = 'localhost'
julius_port = 10500

# create connection for Julius server
j_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
j_socket.connect((julius_host, julius_port))

inputed = ''
while True:
    while (inputed.find('\n.') == -1):
        inputed += j_socket.recv(1024).decode()
    
    #print(inputed)
    for line in inputed.split('\n'):
        print('LINE:' + line)
	
    inputed = ''

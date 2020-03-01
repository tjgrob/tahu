# import the socketserver module of Python
import socketserver

# Create a Request Handler
# In this TCP server case - the request handler is derived from StreamRequestHandler
class MyTCPRequestHandler(socketserver.StreamRequestHandler):

# handle() method will be called once per connection
    def handle(self):
        # Receive and print the data received from client
        print("Recieved one request from {}".format(self.client_address[0]))
        msg = self.rfile.readline().strip()
        print("Data Recieved from client is:".format(msg))
        print(msg)

        # Send some data to client
        self.wfile.write("Hello Client....Got your message".encode())

# Create a TCP Server instance
aServer         = socketserver.TCPServer(("127.0.0.1", 9090), MyTCPRequestHandler)

# Listen for ever
aServer.serve_forever()

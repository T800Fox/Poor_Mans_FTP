class fileServ:
    def __init__(self, aDirectory, aBindingAddress, aHostingPort):
        import socket
        import subprocess
        from multiprocessing import Process

        self.socket = socket
        self.Process = Process
        self.address = aBindingAddress
        self.dirToServ = aDirectory
        self.peripheralPort = 9000
        self.peripherals = []
        self.serveableFiles = []

        # generate list of serveable files:
        buffer = ""
        pointer = 1
        for c in subprocess.check_output(['ls', self.dirToServ]).decode('utf-8'):
            if c != '\n':
                buffer += c
            elif c == '\n':
                self.serveableFiles.append([pointer, buffer])
                pointer += 1
                buffer = ""


        # setup socket:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.address, 9999))
        s.listen(100)

        # mainloop:
        while True:
            c, address = s.accept()
            if c:
                print("New client at " + str(address))

                # tell client files they can download:
                c.send(b'\nList of downloadable files:\n')
                for i in self.serveableFiles:
                    buffer = "    " + "{" + str(i[0]) + "} - " + i[1] + "\n"
                    c.send(str.encode(buffer))

                while c:
                    # wait for client to choose valid file:
                    selection = self.takeSelection(c.recv(1024), c)
                    # send the client the file through peripheral:
                    pfservFront = "pfserv"
                    # if the loop has failed the user inputed the quit character.
                    try:
                        buffer = self.dirToServ + "/" + self.serveableFiles[int(selection) - 1][1]
                        self.addPeripheralOperation(pfservFront + str(self.peripheralPort), "self.peripheralServ", [self.peripheralPort, buffer])
                        buffer = "Broadcasting " + self.serveableFiles[int(selection) - 1][1] +" on port: " + str(self.peripheralPort) + "\n"
                        print(buffer)
                        self.peripheralPort += 1
                        c.send(str.encode(buffer))
                    except:
                        print("Client has quit")
                        c.close()
                        c = False

    # allows for operations to be run separate from the main process:
    def addPeripheralOperation(self, name, functionName, arguments):
        exec("self." + name + " = self.Process(target=" + functionName + ", args=" + str(arguments) + ")")
        exec("self." + name + ".daemon=True")
        exec("self." + name + ".start()")
        self.peripherals.append("self." + name)

    # depedancy for takeSelection, modular way of ensuring a selected file exists in the target directory:
    def fileExists(self, input, fileList):
        for i in fileList:
            if i[0] == input:
                return True
        return False

    # broadcasts a files contents on a secondary socket
    def peripheralServ(self, port, path):
        ps = self.socket.socket()
        ps.setsockopt(self.socket.SOL_SOCKET, self.socket.SO_REUSEADDR, 1)
        ps.bind((self.address, port))
        ps.listen(1)
        while True:
            pc, pAddress= ps.accept()
            if pc:
                f = open(path, 'rb')
                transmit = f.read(1024)
                while transmit:
                    pc.send(transmit)
                    transmit = f.read(1024)

    # modular method for cleaning the clients input:
    def takeSelection(self, byteInput, client):
        while True:
            cleanInput = byteInput.decode('utf-8')
            cleanInput = cleanInput[:-1]
            try:
                if cleanInput == 'q':
                    client.close()
                    return 'q'
                elif self.fileExists(int(cleanInput), self.serveableFiles):
                    return str(cleanInput)
                else:
                    client.send(b'invalid input\n')
            except:
                client.send(b'invalid input\n')
            byteInput = client.recv(1024)



if __name__ == "__main__":
    # get the computer's local IP:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
    localAddress = s.getsockname()[0]
    s.close()

    # start the file broadcaster on the local machine.
    test = fileServ('bunchOfiles', localAddress, 9999)

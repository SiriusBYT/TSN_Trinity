import socket, math, time

def SirioAPI(Request,Server,Port):
    Packet_Size = 8192
    Socket = socket.socket()

    def Log(Log):
        CTime = time.localtime()
        Time = f"{CTime.tm_hour:02d}:{CTime.tm_min:02d}:{CTime.tm_sec:02d}"
        Date = f"{CTime.tm_mday:02d}-{CTime.tm_mon:02d}-{CTime.tm_year}"
        print(f"[{Date} - {Time}] {Log}")

    # Key Handling Functions
    def Send(Packet):
        try: Socket.send(str(Packet).encode())
        except Exception as Error_Info: Log(f"[Error - Sending] {Error_Info}"); return
    def Receive_Data():
        try: Response = Socket.recv(Packet_Size).decode(); return Response
        except Exception as Error_Info: Log(f"[Error - Receiving] {Error_Info}"); return
    
    Ping = time.monotonic()*1000; Socket.connect((Server, Port))
    Ping = math.floor(((time.monotonic()*1000) - Ping))

    Send(Request)
    return Receive_Data(),Ping
    
while True:
    print(SirioAPI(input("api: "),"trinity_raw.sirio-network.com",1407))
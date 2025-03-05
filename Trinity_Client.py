import socket, math, time

from TSN_Abstracter import *;
import threading;

Packet_Size = 8192;

@lambda _: _()
def Client_Key_Private():
    Log.Info("A Private Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Private();

@lambda _: _()
def Client_Key_Public():
    Log.Info("A Public Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Public(Client_Key_Private)

class Trinity_Client:
    def __init__(self, Address, Port, Tickrate: int = 0.01, Shell: bool = False) -> None:
        self.Client = socket.socket();
        self.Address = Address;
        self.Port = Port;
        self.Tickrate = Tickrate;

        self.Secure = False;
        self.Connected = self.Listen = True;
        self.Result_History: list[str] = [];


        self.T_Receive = threading.Thread(target=self.Thread_Receive);
        self.T_Receive.daemon = True;
        self.T_Receive.start();
    
        self.Ping = time.monotonic()*1000; self.Client.connect((self.Address, self.Port));
        self.Ping = math.floor(((time.monotonic()*1000) - self.Ping));
        Log.Info(f"Connected to {self.Address}:{self.Port} with a latency of {self.Ping}ms.");
        
        while (self.Connected and self.Shell):
            Command = input(f"Trinity://");
            if (Command == "SYS¤Encrypt"):
                self.Send(Command);
                self.Enable_Encryption();
            else:
                self.Send(Command);


    def Thread_Receive(self):
        while (self.Connected):
            while (self.Listen):
                New_Message = self.Receive();
                if (New_Message != None):
                    Log.Info(f"{self.Address} -> {New_Message}");
                    self.Result_History.append(New_Message);

    def Terminate(self) -> None:
        S_Close = Log.Info(f"Closing {self.Address}...");
        self.Connected = self.Listen = False;
        try:
            self.Send_Code("CLOSING");
            self.Client.close();
        except:
            Misc.Void();
        S_Close.OK();

    def Enable_Encryption(self) -> None:
        # This code is shit. But I can't be fucked fixing it.
        self.Result_History = [];

        self.Send(Cryptography.Get_Bytes_Public(Client_Key_Public));
        while (self.Result_History == []):
            time.sleep(self.Tickrate);
        self.Server_Public = Cryptography.Load_Public(self.Result_History[0]);
        
        self.Secure = True;
        self.Result_History = [];
        self.Send("Hugging a Mika a day, keeps your sanity away~");
        while (self.Result_History == []):
            print("Waiting...")
            time.sleep(self.Tickrate);
        if (self.Result_History[0] != "CODE¤OK"):
            self.Secure = False;
        self.Result_History = [];

    def Receive(self) -> str:
        try:
            # Receive Data
            if (self.Secure):
                Data = Cryptography.Decrypt(Client_Key_Private, self.Client.recv(Packet_Size));
            else:
                Data = self.Client.recv(Packet_Size).decode();
            return Data;
        
        except Exception as Except:
            Misc.Void();

    def Send(self, Data: str) -> bool:
        def Send_RawSocket(Data: str) -> bool:
            if (self.Secure):
                S_Send = Log.Info(f"{Data} -> {self.Address} (Encrypted)")
                Message = Cryptography.Encrypt(self.Server_Public, Data);
            elif (type(Data) == bytes):
                S_Send = Log.Info(f"{Data} -> {self.Address} (Public Key)")
                Message = Data;
            else:
                S_Send = Log.Info(f"{Data} -> {self.Address} (Unencrypted)")
                Message = Data.encode("UTF-8");

            try:
                self.Client.send(Message);
                S_Send.OK();
                return True;
            except Exception as Except:
                S_Send.ERROR(Except);
                return False;
    
        return Send_RawSocket(Data);

    def Send_Code(self, Message: str) -> bool:
        return self.Send(f"CODE¤{Message}");
    
while True:
    Trinity_Client("localhost", 1407, True);
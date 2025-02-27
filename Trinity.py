from TSN_Abstracter import *;
import asyncio, threading;
import websockets, socket;
import dotenv, os;
import time;


Version: str = "a250221";
Packet_Size: int = 8192;
Server_Running: bool = True;
Server_Max_Communication_Errors: int = 3;
Server_Max_Communication_Length: int = 10;

# Dictionary
    # Trinity Server Types
Relay: int = 0;
Endpoint: int = 1;
Heartbeat: int = 2;

""" MEGA Cursed Syntax I'm aware, these functions are ran once and gives us the Keys for the server.
Gives us the variables "Server_Key_Private" and "Server_Key_Public" which are going to be used to secure communication.
It's better to generate a new key for each client security wise but this is taxing on the server and it doesn't really
matter anyways since the bigger problem is storing the data received rather than the currently on-going communications"""
@lambda _: _()
def Server_Key_Private():
    Log.Info("A Private Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Private();

@lambda _: _()
def Server_Key_Public():
    Log.Info("A Public Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Public(Server_Key_Private)


class Trinity_Socket:
    def __init__(self, Socket, WebSocket: bool, Processor) -> None:
        self.WebSocket = WebSocket;
        self.Processor = Processor;

        self.Communication_Errors: int = 0;

        if (self.WebSocket):
            pass;
        else:
            Client, Address = Socket.accept();
            self.Client = Client;
        
        self.Address = f"{Address[0]}:{Address[1]}";
        self.Address = f"Web://{self.Address}" if (self.WebSocket) else f"Raw://{self.Address}";

        self.Secure = True if (self.WebSocket) else False;
        self.Connected = self.Listen = True;
        self.Queue: list[str] = [];

        self.T_Processor = threading.Thread(target=self.Thread_Processor);
        self.T_Processor.daemon = True;
        self.T_Processor.start();

        self.T_Receive = threading.Thread(target=self.Thread_Receive);
        self.T_Receive.daemon = True;
        self.T_Receive.start();


    def Thread_Processor(self, Tickrate: int = 0.01):
        while (self.Connected):
            if (self.Queue != []):
               if(self.Processor(self, self.Queue[0])):
                   self.Queue.pop(0);
            else:
                time.sleep(Tickrate);

    def Thread_Receive(self):
        while (self.Connected):
            while (self.Listen):
                New_Message = self.Receive();
                if (New_Message != None):
                    Log.Info(f"{self.Address} -> {New_Message}");
                    self.Queue.append(New_Message);
    
    def Thread_Timeout(self):
        # Terminate a client if they're connected for more than an hour.
        time.sleep(Server_Max_Communication_Length);
        self.Send_Code("CONNECTION_LENGTH_EXCEEDED");
        self.Terminate();

    
    def Communication_Failed(self) -> None:
        self.Communication_Errors += 1;
        if (self.Communication_Errors >= Server_Max_Communication_Errors):
            self.Terminate();

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
        self.Listen = False;

        self.Client_Public = self.Receive();
        self.Send(Server_Key_Public);
        
        Data = self.Receive();
        if (Cryptography.Decrypt(self.Server_Private, Data) == "Hugging a Mika a day, keeps your sanity away~"):
            self.Secure = True;

    def Receive(self) -> str:
        try:
            # Receive Data
            if (self.WebSocket):
                Data = self.Client.recv();
            else:
                if (self.Secure):
                    Data = Cryptography.Decrypt(self.Private_Key, self.Client.recv(Packet_Size).decode());
                Data = self.Client.recv(Packet_Size).decode();
            
            # Null Check
            if (Data != ""):
                return Data;
            else:
                self.Communication_Failed();
        
        except Exception as Except:
            self.Communication_Failed();

    def Send(self, Data: str) -> bool:
        def Send_WebSocket(Data: str) -> bool:
            S_Send = Log.Info(f"{Data} -> {self.Address}")
            try:
                self.Client.send(Data);
                S_Send.OK();
                return True;
            except Exception as Except:
                S_Send.ERROR(Except);
                self.Communication_Failed();
                return False;

        def Send_RawSocket(Data: str) -> bool:
            if (self.Secure):
                S_Send = Log.Info(f"{Data} -> {self.Address} (Encrypted)")
                Message = Cryptography.Encrypt(self.Client_Public, Data);
            else:
                S_Send = Log.Info(f"{Data} -> {self.Address} (Unencrypted)")
                Message = Data;
            
            try:
                self.Client.send(Message.encode("utf-8"));
                S_Send.OK();
                return True;
            except Exception as Except:
                S_Send.ERROR(Except);
                return False;
    
        if (self.WebSocket):
            return Send_WebSocket(Data);
        else:
            return Send_RawSocket(Data);

    def Send_Code(self, Message: str) -> bool:
        return self.Send(f"CODE¤{Message}");

# Example Processor
def Echo(Client: Trinity_Socket, Command: str) -> bool:
    Client.Send(Command);
    return True;

class Trinity_Server:
    def __init__(self, Processor, Type: int = Relay) -> None:
        self.Processor = Processor;
        self.Type = Type;

        # You can't use variables in switch cases so we have to use the raw fucking numbers
        match self.Type:
            case 0: # Relay
                Log.Info("Starting Trinity Server as a Relay...")
                Log.Info("Loading Endpoints Configuration...");
                Configuration = File.JSON_Read("Relay.json");
            
                threading.Thread(target=self.RawSocket_Thread()).setDaemon(True).start();
            
            case 1: # Endpoint
                Log.Info("Starting Trinity Server as an Endpoint...")
                pass;
            case 2: # Heartbeat
                Log.Info("Starting Trinity Endpoint Heartbeat...")
                pass;
            case _:
                Log.Critical(f"Unknown Trinity Server Type: {self.Type}. Shutting down.")
                quit();

    def RawSocket_Thread(self, Port: int = 1407) -> None:
        Log.Info("Starting RawSockets Thread...")
        global Socket_Raw;
        Socket_Raw = socket.socket();
        Attempts = 1;
        while True:
            Log.Carriage(f"Attempting to bind RawSocket... (Attempt {Attempts})");
            try:
                Socket_Raw.bind(("0.0.0.0", Port));
                Log.Info(f"Successfully binded RawSocket in {Attempts} Attempts.");
                break;
            except:
                Attempts += 1;
                time.sleep(1);
        S_Listen = Log.Info(f"Listening for RawSockets...");
        Socket_Raw.listen();
        S_Listen.OK();
        while Server_Running:
            Client_Thread = threading.Thread(target=Trinity_Socket(Socket_Raw, False, self.Processor));
            Client_Thread.daemon = True;
            Client_Thread.start();


# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity_Server(Processor=Echo, Type=Relay);
else:
    Trinity_Server(Processor=Echo, Type=Heartbeat);
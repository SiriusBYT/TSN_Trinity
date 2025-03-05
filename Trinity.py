from TSN_Abstracter import *;
import asyncio, threading;
import websockets, socket;
import dotenv, os;
import time, math;


Version: str = "a250221";
Packet_Size: int = 8192;
Server_Running: bool = True;
Server_Max_Communication_Errors: int = 3;
Server_Max_Communication_Length: int = 3600;


""" Make the IDE less angry because of the type safe functions below.
Note these functions would normally be called from another file. """
class Trinity_Socket: pass;

# Example Processor
def Echo(Client: Trinity_Socket, Command: str) -> bool:
    Client.Send(Command);
    return True;

# Example Routine Function
def Echo_Routine(Client: Trinity_Socket):
    while (Client.Connected):
        time.sleep(10);
        while (Client.Listen):
            #Client.Send(f"Routine Message!");
            time.sleep(10);


""" MEGA Cursed Syntax I'm aware, these functions are ran once and gives us the Keys for the server.
Gives us the variables "Key_Private" and "Key_Public" which are going to be used to secure communication.
It's better to generate a new key for each client security wise but this is taxing on the server and it doesn't really
matter anyways since the bigger problem is storing the data received rather than the currently on-going communications"""
@lambda _: _()
def Key_Private():
    Log.Info("A Private Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Private();

@lambda _: _()
def Key_Public():
    Log.Info("A Public Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Public(Key_Private)

class Trinity_Socket:
    def __init__(self, Socket, WebSocket: bool, Processor, Routine, Tickrate: int = 0.01) -> None:
        """NOTE: Processor and Routine are FUNCTIONS! For some reason adding "function" to declare we want to accept a function,
        doesn't FUCKING WORK because Python is retarded or something. This is hateful. We're at the mercy of the user not fucking up."""
        self.WebSocket = WebSocket;
        self.Processor = Processor;
        self.Routine = Routine;
        self.Tickrate = Tickrate;

        self.Communication_Errors: int = 0;
        self.Auth_Level: int = 0;

        if (self.WebSocket):
            pass;
        else:
            Client, Address = Socket.accept();
            self.Client = Client;
        
        self.IP = f"{Address[0]}:{Address[1]}";
        self.Address = f"Web://{self.IP}" if (self.WebSocket) else f"Raw://{self.IP}";
        Log.Info(f"Connection: {self.Address} (Raw)");

        self.Secure = True if (self.WebSocket) else False;
        self.Connected = self.Listen = True;
        self.Queue: list[str | bytes] = [];
        self.Listen_Accident: str = None;

        self.T_Processor = threading.Thread(target=self.Thread_Processor);
        self.T_Processor.daemon = True;
        self.T_Processor.start();

        self.T_Receive = threading.Thread(target=self.Thread_Receive);
        self.T_Receive.daemon = True;
        self.T_Receive.start();
    
        self.T_Timeout = threading.Thread(target=self.Thread_Timeout);
        self.T_Timeout.daemon = True;
        self.T_Timeout.start();

        self.Routine(self);

    def Thread_Processor(self):
        while (self.Connected):
            if (self.Queue != []):
               if (self.Queue[0] == "SYS¤Encrypt"):
                   self.Enable_Encryption();
               elif (self.Processor(self, self.Queue[0])):
                   self.Queue.pop(0);
            else:
                time.sleep(self.Tickrate);

    def Thread_Receive(self):
        # This system is retarded but works. Mostly cause it only has issues with Enable_Encryption()
        while (self.Connected):
            while (self.Listen):
                New_Message = self.Receive();
                if (New_Message != None):
                    Log.Info(f"{self.Address} -> {New_Message}");
                    self.Queue.append(New_Message);
                time.sleep(self.Tickrate);
            time.sleep(self.Tickrate);
    
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
        # This code is shit. But I can't be fucked fixing it.
        self.Queue = [];
        while (self.Queue == []):
            time.sleep(self.Tickrate);
        
        self.Client_Public = Cryptography.Load_Public(self.Queue[0]);
        self.Queue.pop(0);
        self.Send(Cryptography.Get_Bytes_Public(Key_Public));
        
        self.Secure = True;

        while (self.Queue == []):
            time.sleep(self.Tickrate);
        if (self.Queue[0] == "Hugging a Mika a day, keeps your sanity away~"):
            self.Send_Code("OK");
        else:
            self.Send_Code("DECRYPTED_UNEXPECTED");
            self.Secure = False;
        self.Queue.pop(0);

    def Receive(self) -> str:
        try:
            # Receive Data
            if (self.WebSocket):
                Data = self.Client.recv();
            else:
                if (self.Secure):
                    Data = Cryptography.Decrypt(Key_Private, self.Client.recv(Packet_Size));
                else:
                    Data = self.Client.recv(Packet_Size).decode();
            
            # Null Check
            if (Data != ""):
                return Data;
            else:
                self.Communication_Failed();
        
        except Exception as Except:
            self.Communication_Failed();

    def Send(self, Data: str | bytes) -> bool:
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

        def Send_RawSocket(Data: str | bytes) -> bool:
            if (self.Secure):
                S_Send = Log.Info(f"{Data} -> {self.Address} (Encrypted)")
                Message = Cryptography.Encrypt(self.Client_Public, Data);
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
    
        if (self.WebSocket):
            return Send_WebSocket(Data);
        else:
            return Send_RawSocket(Data);

    def Send_Code(self, Message: str) -> bool:
        return self.Send(f"CODE¤{Message}");

class Trinity_Server:
    def __init__(self, Processor, Routine, Type: str = "Relay") -> None:
        self.Processor = Processor;
        self.Routine = Routine;
        self.Type = Type;

        # You can't use variables in switch cases so we have to use the raw fucking numbers
        match self.Type:
            case "Relay": # Relay
                Log.Info("Starting Trinity Server as a Relay...")
                Log.Info("Loading Endpoints Configuration...");
                Configuration = File.JSON_Read("Relay.json");
            
                threading.Thread(target=self.RawSocket_Thread()).setDaemon(True).start();
            
            case "Endpoint":
                Log.Info("Starting Trinity Server as an Endpoint...")
                pass;
            case "Heartbeat":
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
            Client_Thread = threading.Thread(target=Trinity_Socket(Socket_Raw, False, self.Processor, self.Routine));
            Client_Thread.daemon = True;
            Client_Thread.start();

class Trinity_Client(Trinity_Socket):
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

    def Enable_Encryption(self) -> None:
        # This code is shit. But I can't be fucked fixing it.
        self.Result_History = [];

        self.Send(Cryptography.Get_Bytes_Public(Key_Public));
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

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity_Server(Processor=Echo, Routine=Echo_Routine, Type="Relay");
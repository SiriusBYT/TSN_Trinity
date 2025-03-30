from TSN_Abstracter import *;

import asyncio;

import websockets;
from websockets.sync.server import serve;
from websockets.sync.client import connect;

import dotenv;
import time, math;


Version: str = "a250329";
# Turn these into a dict later that can be read/modified via JSON
Packet_Size: int = 8192;
Server_Running: bool = True;
Server_Max_Communication_Errors: int = 3;
Server_Max_Communication_Length: int = 3600;

""" Make the IDE less angry because of the type safe functions/variables below. """
class Trinity_Server: pass;
Connected_Clients: list[Trinity_Server] = [];

def Trinity_Relayer(Client: Trinity_Server, Command: str) -> bool:
    Client.Send(Command);
    return True;

def Trinity_Routine() -> None:
    while (Server_Running):
        Log.Carriage(f"Connected Clients: {len(Connected_Clients)} // {[str(Client) for Client in Connected_Clients]}");
        time.sleep(1);

""" MEGA Cursed Syntax I'm aware, these functions are ran once and gives us the Keys for the server.
Gives us the variables "Key_Private" and "Key_Public" which are going to be used to secure communication.
It's better to generate a new key for each client security wise but this is taxing on the server and it doesn't really
matter anyways since the bigger problem is storing the data received rather than the currently on-going communications"""
""" # No longer required due to switch to websockets exclusively
@lambda _: _()
def Key_Private():
    Log.Info("A Private Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Private();

@lambda _: _()
def Key_Public():
    Log.Info("A Public Key is being generated for this session. Please hold.");
    return Cryptography.Generate_Public(Key_Private);
"""


class Trinity_Socket:
    def __init__(
            self, 
            Processor = None,
            WebSocket = None,
            Address: str = "ws://localhost:8080",
            Tickrate: int = 0.01,
            **kwargs: dict[str, dict]
        ):
        """NOTE: Processor is a FUNCTION! For some reason adding "function" to declare we want to accept a function,
        doesn't FUCKING WORK because Python is retarded or something. This is hateful. We're at the mercy of the user not fucking up."""
        Connected_Clients.append(self);
        self.Socket = WebSocket;
        self.Address: str = f"{self.Socket.remote_address[0]}:{self.Socket.remote_address[1]}" if (WebSocket != None) else Address;

        self.Processor = Processor;
        self.Tickrate: int = Tickrate;

        self.Communication_Errors: int = 0;
        self.Auth_Level: int = 0;

        self.Connected = self.Process_Auto = True;
        self.Queue: list[str] = [];

        self.kwargs: dict = kwargs;

        self.Configuration();
        self.Thread_Receive();
    
    def __str__(self):
        return f"{self.Address} ¤ {self.Auth_Level} // {self.Queue}";

    def Queue_Wait(self) -> None:
        """ Wait until the queue is no longer empty
        This function is blocking on purpose. """
        while (len(self.Queue) == 0):
            time.sleep(self.Tickrate);
        return;

    def Configuration(self) -> None:
        Log.Critical("Trinity Socket was Initialized without any configuration!");
        self.Connected = False;
        Connected_Clients.remove(self);

    def Send(self, Data: str | bytes) -> bool:
        S_Send = Log.Info(f"{Data} -> {self.Address}")
        try:
            self.Socket.send(Data);
            S_Send.OK();
            return True;
        except Exception as Except:
            S_Send.ERROR(Except);
            self.Communication_Failed();
            return False;

    def Terminate(self) -> None:
        S_Close = Log.Info(f"Closing {self.Address}...");
        self.Connected: bool = False;
        self.Process_Auto: bool = False;
        try:
            self.Send_Code("CLOSING");
            self.Client.close();
        except:
            Misc.Void();
        S_Close.OK();
        Connected_Clients.remove(self);


    def Send_Code(self, Message: str) -> bool:
        return self.Send(f"CODE¤{Message}");

    def Communication_Failed(self) -> None:
        Log.Debug(f"{self.Address} [!] {Log.Get_Caller(3)}()");
        self.Communication_Errors += 1;
        if (self.Communication_Errors >= Server_Max_Communication_Errors):
            self.Terminate();

    def Thread_Receive(self):
        try:
            for Request in self.Socket:
                if (Request != ""):
                    Log.Info(f"{self.Address} <- {Request}");
                    self.Queue.append(Request);
        except:
            self.Communication_Failed();
    
    def Thread_Processor(self):
        while (self.Connected):
            if (self.Queue != []):
               if (self.Queue[0] == "CODE¤Closing"):
                   self.Terminate();
               else:
                   if (self.Process_Auto):
                       if (self.Processor(self, self.Queue[0])):
                           self.Queue.pop(0);
                   else:
                       time.sleep(self.Tickrate);
            else:
                time.sleep(self.Tickrate);
    
    def Thread_Timeout(self):
        # Terminate a client if they're connected for more than an hour by default.
        time.sleep(Server_Max_Communication_Length);
        self.Send_Code("CONNECTION_LENGTH_EXCEEDED");
        self.Terminate();

class Trinity_Server(Trinity_Socket):
    def Configuration(self) -> None:
        Log.Info(f"Connection: {self.Address}");

        Misc.Thread_Start(self.Thread_Processor);
        Misc.Thread_Start(self.Thread_Timeout);



class Trinity_Client(Trinity_Socket):
    def Configuration(self) -> None:
        self.Ping = time.monotonic()*1000;
        self.Socket = connect(self.Address);
        self.Ping = math.floor(((time.monotonic()*1000) - self.Ping));
        self.Interactive = self.kwargs["Shell"];
        Log.Info(f"Connected to {self.Address} with a latency of {self.Ping}ms.");

        Misc.Thread_Start(self.Thread_Shell)

    def Thread_Shell(self) -> None:
        while (self.Connected and self.Interactive):
            Command = input(f"Trinity://");
            self.Send(Command);

    def Communication_Failed(self) -> None: return;





class Trinity_Ignition:
    def __init__(self, Processor, Routine, Type: str = "Relay") -> None:
        self.Processor = Processor;

        match Type:
            case "Relay": # Relay
                Log.Info("Starting Trinity Server as a Relay...")
                Log.Info("Loading Endpoints Configuration...");
                Configuration = File.JSON_Read("Relay.json");

                asyncio.run(self.WebSocket_Thread());
                Routine();

            case "Endpoint":
                Log.Info("Starting Trinity Server as an Endpoint...")
                pass;
            case "Heartbeat":
                Log.Info("Starting Trinity Endpoint Heartbeat...")
                pass;
            case _:
                Log.Critical(f"Unknown Trinity Server Type: {self.Type}. Shutting down.")
                quit();


    async def WebSocket_Thread(self, Port: int = 440) -> None:
        Log.Info("Started WebSockets Thread.");
        def Web_Threader(WebSocket) -> None:
            Trinity_Server(self.Processor, WebSocket);

        with serve(Web_Threader, "0.0.0.0", 8080) as WS:
            WS.serve_forever();

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity_Ignition(Processor=Trinity_Relayer, Routine=Trinity_Routine, Type="Relay");
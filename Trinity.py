from TSN_Abstracter import *;

import asyncio;

import websockets;
from websockets.sync.server import serve;
from websockets.sync.client import connect;

import dotenv;
import time, math;

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
        self.Socket = WebSocket;
        if (self.Socket != None):
            Connected_Clients.append(self);
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
                if (not self.Connected):
                    return;
        except websockets.exceptions.ConnectionClosedError:
            Log.Warning(f"Disconnected: {self.Address}")
            self.Terminate();
        except Exception as Except:
            Log.Warning(Except);
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
        try:
            self.Socket = connect(self.Address);
        except:
            self.Connected: bool = False;
            return;
        self.Ping = math.floor(((time.monotonic()*1000) - self.Ping));
        self.Interactive = self.kwargs["Shell"];
        Log.Info(f"Connected to {self.Address} with a latency of {self.Ping}ms.");

        Misc.Thread_Start(self.Thread_Processor);

        if (self.Interactive):
            Misc.Thread_Start(self.Thread_Shell);

    def Thread_Shell(self) -> None:
        while (self.Connected and self.Interactive):
            Command = input(f"Trinity://");
            self.Send(Command);
            if (Command == "CODE¤Closing"):
                return;

    def Communication_Failed(self) -> None: return;





class Trinity_Ignition:
    def __init__(self, Processor = None, Routine = None, Type: str = "Relay") -> None:
        self.Processor = Processor;

        match Type:
            case "Relay": # Relay
                Log.Info("Starting Trinity Server as a Relay")
                self.Processor = self.Trinity_Relayer if (Processor == None) else Processor;
                self.Routine = self.Trinity_Routine if (Routine == None) else Routine;

                Log.Info("Loading Endpoints Configuration");
                self.Configuration: dict = File.JSON_Read("Relay.json");
                Log.Debug("Loading Nodes")
                self.Nodes: dict = {};
                for Node in self.Configuration["Nodes"]:
                    self.Nodes[Node] = {
                        "Connected": False,
                        "Socket": None,
                    };

                global Packet_Size, Server_Max_Communication_Errors, Server_Max_Communication_Length;
                Log.Debug("Loading Relay Settings")
                Packet_Size = self.Configuration["Settings"]["Packet_Size"];
                Server_Max_Communication_Errors = self.Configuration["Settings"]["Server_Max_Communication_Errors"];
                Server_Max_Communication_Length = self.Configuration["Settings"]["Server_Max_Communication_Length"];

                Misc.Thread_Start(self.WebSocket_Thread);
                self.Routine();

            case "Endpoint":
                Log.Info("Starting Trinity Server as an Endpoint")
                pass;
            case "Heartbeat":
                Log.Info("Starting Trinity Endpoint Heartbeat")
                pass;
            case _:
                Log.Critical(f"Unknown Trinity Server Type: {self.Type}. Shutting down.")
                quit();
    
    def Node_Reconnect(self) -> None:
        Log.Debug("Reconnecting Nodes")
        for Node in self.Configuration["Nodes"]:
            if (self.Nodes[Node]["Connected"] == False):
                Log.Debug(f"Attempting to reestablish link with {Node}.")
                Misc.Thread_Start(
                    self.Node_Thread,
                    (Node, self.Configuration["Nodes"][Node]["Address"])
                );
        Log.Debug("Done attempting to reconnect nodes.")

    def Node_Thread(self, Node_Name: str, Node_Address: str) -> None:
        try:
            self.Nodes[Node_Name]["Socket"] = Trinity_Client(Address=Node_Address);
            while (self.Nodes[Node_Name]["Socket"].Connected == True):
                self.Nodes[Node_Name]["Connected"] = True;
                time.sleep(60)
        except: Misc.Void();
        Log.Critical(f"Node {Node_Name} is down!")
        self.Nodes[Node_Name]["Connected"] = False;


    def WebSocket_Thread(self, Port: int = 8080) -> None:
        Log.Info("Started WebSockets Thread.");
        def Web_Threader(WebSocket) -> None:
            Trinity_Server(self.Processor, WebSocket);

        with serve(Web_Threader, "0.0.0.0", Port) as WS:
            WS.serve_forever();
    
    def Trinity_Relayer(self, Client: Trinity_Server, Command: str) -> bool:
        """
        True = Processed Request Successfully
        False = Need to retry processing due to internal error
        """

        # Make sure the request is in a valid format
        if ("¤" in Command):
            Command = Command.split("¤", 1);
        else:
            Client.Send_Code("INVALID_FORMAT");
            return True;
        if (Command[0] == "Trinity"):
            match Command[1]:
                case "Version":
                    Client.Send(Trinity_Version)
                case "Uptime":
                    Client.Send(Trinity_LUnix);
        return True;

    def Trinity_Routine(self) -> None:
        Reconnect_Delay: int = 60;
        Delay_Tick: int = 60;
        while (Server_Running):
            if (Delay_Tick == Reconnect_Delay):
                Delay_Tick: int = 0
                Nodes_Connected: int = 0;
                for Node in self.Nodes:
                    if (self.Nodes[Node]["Connected"] == True):
                        Nodes_Connected+=1;
                self.Node_Reconnect();

            for Client in Connected_Clients:
                if (not Client.Connected):
                    Connected_Clients.remove(Client);
            Log.Carriage(f"[Nodes: {Nodes_Connected}/{len(self.Configuration["Nodes"])}] - [Clients: {len(Connected_Clients)}]");
            time.sleep(1);
            Delay_Tick+=1;



Trinity_Version: str = "a250330";
Trinity_LUnix: int = Time.Get_Unix();
Connected_Clients: list[Trinity_Server] = [];
Server_Running: bool = True;

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity_Ignition(Type="Relay");
from TSN_Abstracter import *;

import websockets;
from websockets.sync.server import serve;
from websockets.sync.client import connect;

import time, math, psutil, uuid;

class Trinity_Socket:
    def __init__(
            self, 
            Processor = None,
            WebSocket = None,
            Config: dict = {},
            Address: str = "ws://localhost:8080",
            **kwargs: dict[str, dict]
        ):
        """NOTE: Processor is a FUNCTION! For some reason adding "function" to declare we want to accept a function,
        doesn't FUCKING WORK because Python is retarded or something. This is hateful. We're at the mercy of the user not fucking up."""
        self.kwargs: dict = kwargs;

        # Node Shenanigans (JANKY!!!)
        self.ID: str = self.kwargs.get("ID");
        if (self.ID != None): Log.Debug(f"This Socket was created with ID {self.ID}.");
        if (self.kwargs.get("is_Node") == True): Connected_Nodes.append(self);

        self.Socket = WebSocket;

        if (self.Socket != None and Address == "ws://localhost:8080"):
            Connected_Clients.append(self);

        self.Address: str = f"{self.Socket.remote_address[0]}:{self.Socket.remote_address[1]}" if (WebSocket != None) else Address;
        self.Last_Sent: str = "";

        self.Processor = Processor;
        self.Config = Config;

        self.Communication_Errors: int = 0;
        self.Auth_Level: int = 0;

        self.Connected = self.Process_Auto = True;
        self.Queue: list[str] = [];

        self.Configuration();
        self.Thread_Receive();
    
    def __str__(self):
        return f"{self.Address} ¤ {self.Auth_Level} // {self.Queue}";

    def Queue_Wait(self) -> None:
        """ Wait until the queue is no longer empty
        This function is blocking on purpose. """
        while (len(self.Queue) == 0):
            time.sleep(self.Config["Tick_Rate"]);
        return;

    def Configuration(self) -> None:
        Log.Critical("Trinity Socket was Initialized without any configuration!");
        self.Connected = False;
        Connected_Clients.remove(self);

    def Send(self, Data: str) -> bool:
        S_Send = Log.Info(f"{Data} -> {self.Address}");
        try:
            self.Socket.send(Data);
            S_Send.OK();
            self.Last_Sent: str = Data;
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
        if (self.Communication_Errors >= self.Config["Server_Max_Communication_Errors"]):
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
            Log.Debug(f"Error receiving data from {self.Address}:\nEXCEPTION:\n\t{Except}");
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
                       time.sleep(self.Config["Tick_Rate"]);
            else:
                time.sleep(self.Config["Tick_Rate"]);
    
    def Thread_Timeout(self):
        # Terminate a client if they're connected for more than an hour by default.
        time.sleep(self.Config["Server_Max_Communication_Length"]);
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
        except Exception as Except:
            Log.Critical(f"Exception while connecting to {self.Address}:\nEXCEPTION:\n\t{Except}");
            self.Connected: bool = False;
            return;
        self.Ping = math.floor(((time.monotonic()*1000) - self.Ping));
        self.Interactive = self.kwargs.get("Shell");
        Log.Info(f"Connected to {self.Address} with a latency of {self.Ping}ms.");

        Misc.Thread_Start(self.Thread_Processor);

        if (self.Interactive == True):
            Misc.Thread_Start(self.Thread_Shell);

    def Thread_Shell(self) -> None:
        while (self.Connected and self.Interactive):
            Command = input(f"Trinity://");
            if (Command != ""): self.Send(Command);
            if (Command == "CODE¤Closing"): return;

    def Communication_Failed(self) -> None: return;

class Trinity_Requester(Trinity_Socket):
    def __init__(
            self, 
            Request: str,
            Origin: str,
            Address: str = "ws://localhost:8080"
        ):
        self.Request: str = Request;
        self.Origin: str = Origin;
        self.Address: str = Address;
    
    def Requester(self) -> str:
        try:
            self.Socket = connect(self.Address);
            self.Send(f"{self.Origin}¤{self.Request}");
            for Request in self.Socket:
                if (Request != ""):
                    Log.Info(f"{self.Address} <- {Request}");
                    return Request;
        except:
            return "CODE¤ENDPOINT_OFFLINE";

    def Thread_Processor(self): return;



class Trinity_Ignition:
    def __init__(self, Processor = None, Routine = None, Type: str = "Relay") -> None:
        self.Type: str = Type;

        Log.Info(f"Starting Trinity Server as: {self.Type}")
        self.Processor = self.Trinity_Relayer if (Processor == None) else Processor;
        self.Routine = self.Trinity_Routine if (Routine == None) else Routine;

        Log.Info(f"Loading {Type} Config");
        self.Config: dict = File.JSON_Read(f"{self.Type}.json");
        
        Log.Debug(f"Loading {self.Type} Settings")
        global Packet_Size, Tick_Rate, Server_Max_Communication_Errors, Server_Max_Communication_Length;
        self.Address = self.Config["Settings"]["Address"];
        self.Port = self.Config["Settings"]["Port"];
        Packet_Size = self.Config["Settings"]["Packet_Size"];
        Tick_Rate = self.Config["Settings"]["Tick_Rate"];
        Server_Max_Communication_Errors = self.Config["Settings"]["Server_Max_Communication_Errors"];
        Server_Max_Communication_Length = self.Config["Settings"]["Server_Max_Communication_Length"];

        match Type:
            case "Relay": # Relay
                Log.Debug("Loading Nodes")
                self.Nodes: dict = {};
                for Node in self.Config["Nodes"]:
                    self.Nodes[Node] = {
                        "Connected": False,
                        "Heartbeat": "OFFLINE"
                    };

                Misc.Thread_Start(self.WebSocket_Thread);
                self.Routine();
            case "Endpoint":
                Misc.Thread_Start(self.WebSocket_Thread);
                self.Routine();
            case "Heartbeat":
                Log.Info("Starting Trinity Endpoint Heartbeat")
                pass;
            case _:
                Log.Critical(f"Unknown Trinity Server Type: {self.Type}. Shutting down.")
                quit();



    def Node_Reconnect(self) -> None:
        Log.Debug("Reconnecting Nodes")
        for Node in self.Config["Nodes"]:
            if (self.Nodes[Node]["Connected"] == False):
                Log.Debug(f"Attempting to reestablish link with {Node}.")
                Misc.Thread_Start(
                    self.Node_Thread,
                    (Node, self.Config["Nodes"][Node]["Address"])
                );
        Log.Debug("Done attempting to reconnect nodes.")

    def Node_Thread(self, Node_Name: str, Node_Address: str) -> None:
        def Node_Processor(Node: Trinity_Client, Command: str):
            Command = Command.split("¤", 1);
            Destination: str = Command[0];
            if (Destination == "ALL"):
                for Client in Connected_Clients:
                    Client.Send(f"{Node_Name}¤{Command}");
            else:
                for Client in Connected_Clients:
                    if (Destination == Client.Address):
                        Client.Send(f"{Node_Name}¤{Command}");
            Node.Queue.pop(0);
        
        def Node_Threader(Node_Address: str, Node_ID: str) -> None:
            Trinity_Client(Processor=Node_Processor, Address=Node_Address, Config=self.Config["Settings"], ID=Node_ID, is_Node=True);
        # This got to be the worst code I've ever written. Not even Mika would xd at this.
        try:
            Node_Socket = None;
            Node_ID = str(uuid.uuid4());
            time.sleep(1); # Funny race condition
            Misc.Thread_Start(Node_Threader, (Node_Address, Node_ID));
            time.sleep(1); # Funny race condition
            for Node in Connected_Nodes:
                if (Node.ID == Node_ID):
                    Node_Socket = Node;
                    break;
        except Exception as Except:
            raise Exception(Except);
    
        if (Node_Socket == None):
            raise Exception("Could not find ID in Connected Nodes!");
    
        while (Node_Socket.Connected == True):
            self.Nodes[Node_Name]["Connected"] = True;
            time.sleep(2);
            Log.Debug(f"{Node_Name} Queue: {Node_Socket.Queue}");
        Log.Critical(f"Node {Node_Name} is down!")
        self.Nodes[Node_Name]["Connected"] = False;



    def WebSocket_Thread(self) -> None:
        Log.Info("Started WebSockets Thread.");
        def Web_Threader(WebSocket) -> None:
            Trinity_Server(self.Processor, WebSocket, self.Config["Settings"]);

        with serve(Web_Threader, self.Address, self.Port) as WS:
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
    
        # Internal Relay Commands
        if (Command[0] == "Trinity"):
            match Command[1]:
                case "Version":
                    Client.Send(Trinity_Version);
                case "Heartbeat":
                    Client.Send(f"{psutil.cpu_percent(0.01)}¤{psutil.virtual_memory().available}¤{psutil.virtual_memory().total}")
                case "Uptime":
                    Client.Send(str(Trinity_LUnix));
                case _:
                    Client.Send_Code("INVALID_COMMAND");
        else:
            if (Command[0] in self.Nodes):
                Client.Send(Trinity_Requester(Command[1], Client.Address, self.Config["Nodes"][Command[0]]["Address"]).Requester());
            else:
                Client.Send_Code("ENDPOINT_UNKNOWN");
        return True;

    def Trinity_Routine(self) -> None:
        Reconnect_Delay: int = 8;
        Delay_Tick: int = 8;
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
            Log.Carriage(f"[Nodes: {Nodes_Connected}/{len(self.Config["Nodes"])}] - [Clients: {len(Connected_Clients)}]");
            time.sleep(1);
            Delay_Tick+=1;


Trinity_Version: str = "a250330";
Trinity_LUnix: int = Time.Get_Unix(); # Unix Time of when Server Launched, calculation of uptime is done client side.
Connected_Clients: list[Trinity_Server] = [];
Connected_Nodes: list[Trinity_Client] = [];
Server_Running: bool = True;

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 20; # Show ALL messages
    Trinity_Ignition(Type="Relay");
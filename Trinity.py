from TSN_Abstracter import *;
import asyncio, threading;
import websockets, socket;
import dotenv, os;

import time

Version = "a250221";
Packet_Size = 8192;

class Trinity_Socket:
    def __init__(self, Client, Address, WebSocket: bool) -> None:
        self.Client = Client;
        self.WebSocket = WebSocket;

        self.Address = f"{Address[0]}:{Address[1]}";
        self.Address = f"Web://{self.Address}" if (self.WebSocket) else f"Raw://{self.Address}";

        self.Secure = True if (self.WebSocket) else False;
        self.Connected = self.Listen = True;
        self.Last_Message = None;
        threading.Thread(target=self.Async_Receive).start();

    def Async_Receive(self):
        while (self.Connected):
            while (self.Listen):
                self.Last_Message = self.Receive();
                Log.Info(f"{self.Address} -> {self.Last_Message}");

    def Receive(self) -> str:
        if (self.WebSocket):
            return self.Client.recv();
        else:
            if (self.Secure):
                return Cryptography.Decrypt(self.Private_Key, self.Client.recv(Packet_Size).decode());
            return self.Client.recv(Packet_Size).decode();

    def Send(self, Data: str) -> bool:
        def Send_WebSocket() -> bool:
            S_Send = Log.Info(f"{Data} -> {self.Address}")
            try:
                self.Client.send(Data);
                S_Send.OK();
                return True;
            except Exception as Except:
                S_Send.ERROR(Except);
                return False;

        def Send_RawSocket() -> bool:
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

    def Enable_Encryption(self) -> None:
        self.Listen = False;

        self.Server_Private, self.Server_Public = Cryptography.Generate_Key();
        self.Client_Public = self.Receive();
        self.Send(self.Server_Public);
        
        Data = self.Receive();
        if (Cryptography.Decrypt(self.Server_Private, Data) == "Hugging a Mika a day, keeps your sanity away~"):
            self.Secure = True;


class Trinity_Server:
    def __init__(self) -> None:
        Log.Info("Loading Relayed Servers...");
        Configuration = File.JSON_Read("Relay.json");

    def RawSocket_Thread(self) -> None:
        async def Listener() -> None:
            RawSocket = await asyncio.start_server(Trinity_Socket, 'localhost', 1407);
            async with RawSocket:
                await RawSocket.serve_forever();

        asyncio.run(Listener());

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity();
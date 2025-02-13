# Server Modules
import socket # API's Native Language 
import websockets # API's Translated Language
import ssl # Required for WebSockets BS
import urllib.request # Required for CORS Proxy

# Multi-threading modules
import asyncio # Required for WebSockets
import _thread # Required for multi-client raw socket clients.
import threading # Required for WebSockets

# Miscellaneous Modules
import time # Required for logs
import os # Required for KeyboardInterrupt (DEBUG) and loading config files
import sys # Required for KeyboardInterrupt (DEBUG)
import configparser # Load the back-end server config file
import json # Load the list of servers to redirect to
import traceback # Error handling

# Load sensitive information
import dotenv
dotenv.load_dotenv()

# Own Modules
from SN_PyDepends import *
from SN_APIC import *

Log(f'[System] Configuring server...')
SRV_CFG = LoadCFG(os.path.basename(__file__).replace(".py", ".cfg"))

""" .env Variables """
SSL_Cert = os.getenv('SSL_Cert')
SSL_Key = os.getenv('SSL_Key')

""" .cfg Variables """
SRV_Name = SRV_CFG["Info"]["Name"]
SRV_Desc = SRV_CFG["Info"]["Description"]
SRV_Vers = SRV_CFG["Info"]["Version"]

Routine_Sleep = int(SRV_CFG["API"]["RoutineSleep"])
API_RawPort = int(SRV_CFG["API"]["RawPort"])
API_WebPort = int(SRV_CFG["API"]["WebPort"])
API_PacketSize = int(SRV_CFG["API"]["PacketSize"])

""" Processed Variables """
API_SocketHost = socket.gethostname()
API_RawSocket = socket.socket()

SSL_Options = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
SSL_Options.load_cert_chain(SSL_Cert, keyfile=SSL_Key)

with open("servers.json", "r", encoding="UTF-8") as Entries:
    APIs = json.load(Entries)

Log(f'[System] Loaded configuration for "{SRV_Name} - {SRV_Vers}", {SRV_Desc}.')


""" Service Functions """
def SirioAPI_Thread():
    Log(f'[System] INFO: Initializing SirioAPI...')

    async def Server_Redirect(Client_Request,Client_Address):
        Client_Request = Client_Request.split("://")
        Client_Address = Client_Address.split(":")
        if len(Client_Request) >= 2:
            for API in APIs:
                if Client_Request[0].upper() == API.upper():
                    Log(f'[Forwarding] "{Client_Request[0]} API": {Client_Request[1]}')
                    return str(SirioAPI(f"{Client_Address[0]}¤{Client_Request[1]}", APIs[API]["Address"], APIs[API]["Port"])[0]) # Janky!
            Log(f'[ERROR] API Not Found: "{str(Client_Request)}" !')
            return "API_NOT-FOUND"
        else:
            Log(f'[ERROR] Invalid Request: "{str(Client_Request)}" !')
            return "INVALID_REQUEST"
        
    """ Socket Handlers """
    def RawSocket_Server():
        Log(f'[System] INFO: Starting RawSockets Server...')

        async def RawSocket_Handler(Client_Socket):
            Client, Address = Client_Socket.accept()
            Client_Address = str(Address[0])+":"+str(Address[1])
            Log(f'[Connection] OK: Raw://{Client_Address}.')

            Client_Request = Client.recv(API_PacketSize).decode()
            Log(f'[Request] Raw://{Client_Address}: "{Client_Request}".')
            Server_Result = await Server_Redirect(Client_Request,Client_Address)

            Log(f'[Sending] Raw://{Client_Address}: {Server_Result[0]}')
            Client.send(Server_Result[0].encode())

        def RawSocket_Async(RawSocket):
            asyncio.run(RawSocket_Handler(RawSocket))

        Log(f'[System] OK: RawSockets thread started.')
        Attempt = 1
        while True:
            try:
                API_RawSocket.bind((API_SocketHost, API_RawPort))
                Log(f"[System] Success: Binded RawSocket Server in {Attempt} attempt(s).")
                break
            except:
                Log(f"[System] ERROR: Failed to bind RawSocket Server! (Attempt {Attempt})")
                Attempt+=1
                time.sleep(1)
        API_RawSocket.listen()
        Log(f'[System] OK: Now listening for RawSockets.')
        while True:
            threading.Thread(target=RawSocket_Async(API_RawSocket)).start()

    def WebSocket_Server():
        Log(f'[System] INFO: Starting WebSockets Server...')

        async def Websocket_Handler(Client):
            # Make the client connection readable
            Address = Client.remote_address
            Client_Address = str(Address[0])+":"+str(Address[1])

            Log(f'[Connection] OK: Web://{Client_Address}.')
            
            Client_Request = await Client.recv()
            Log(f'[Request] Web://{Client_Address}: "{Client_Request}".')
            Server_Result = await Server_Redirect(Client_Request,Client_Address)
            Log(f'[Sending] Web://{Client_Address}: {Server_Result}')
            await Client.send(Server_Result)

        async def Websocket_Listener():
            Log(f'[System] OK: WebSockets thread started.')
            async with websockets.serve(Websocket_Handler, "0.0.0.0", API_WebPort, ssl=SSL_Options):
                await asyncio.Future()
        asyncio.run(Websocket_Listener())

    threading.Thread(target=RawSocket_Server).start()
    threading.Thread(target=WebSocket_Server).start()


""" Server State Functions """

def Shutdown():
    Log(f'[System] SHUTDOWN: Shutting down server...')
    DWeb_Title = f'The "{SRV_Name}" Server is offline!'
    DWeb_Desc = "Trinity is the Front-End Server for the Sirio Network API. All services such as the Flashcord API, Sirio News API and etc are now unreachable! <@311057290562371586> will soon provide more information."
    # DWeb_Send(DWeb_Title, DWeb_Desc, "Public")
    try: sys.exit(130)
    except SystemExit: os._exit(130)
    
def Bootstrap():
    os.system("clear")
    Log(f"[System] Starting server...")
    threading.Thread(target=SirioAPI_Thread).start()
    Log(f'[System] Server initialized.')
    DWeb_Title = f'The "{SRV_Name}" Server is now online!'
    DWeb_Desc = "Trinity is the Front-End Server for the Sirio Network API. All services such as the Flashcord API, Sirio News API and etc are now accessible."
    # DWeb_Send(DWeb_Title, DWeb_Desc, "Public")
    try:
        while True: 
            Log(f'[System] Awaiting next Routine Loop in {Routine_Sleep} seconds.')
            time.sleep(Routine_Sleep)
            Log(f'[System] Executing Routine.')
    except KeyboardInterrupt:
        Shutdown()

# Spark
if __name__== '__main__': 
    while True:
        try: Bootstrap()
        except Exception: Crash(traceback.format_exc(),False)

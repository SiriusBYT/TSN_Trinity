from TSN_Abstracter import *;
import asyncio, threading;
import websockets, socket;
import dotenv, os;

import time

class Trinity:
    def __init__(self):
        Log.Info("Configuring Trinity Relay...");
        time.sleep(2);
        Log.Status_Update("[OK]");
        Log.Info("Starting Trinity Relay...");
        time.sleep(2);
        Log.Status_Update("[OK]");

# If the file is ran as is, assuming we want to start the Trinity Relay.
if (__name__== "__main__"):
    Log.Delete(); # DEBUG

    Config.Logging["File"] = True; # Allow Log Files
    Config.Logging["Print_Level"] = 0; # Show ALL messages
    dotenv.load_dotenv()
    Trinity();
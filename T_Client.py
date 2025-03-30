# This file imports Trinity and runs its client.
from TSN_Abstracter import *; Log.Clear();
from Trinity import *;

def Client_Processor(Socket: Trinity_Client, Reply: str) -> bool:
    Log.Info(f"The Trinity Relay at {Socket.Address} sent us \"{Reply}\".");
    return True;

Trinity_Client(Processor=Client_Processor, Shell=True);
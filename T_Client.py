# This file imports Trinity and runs its client.
from TSN_Abstracter import *; Log.Clear();
from Trinity import *;

def Client_Processor(Socket: Trinity_Client, Reply: str) -> bool:
    match Socket.Last_Sent:
        case "Trinity¤Uptime":
            Log.Info(f"The Trinity Relay was up for a total of {Time.Elapsed_String(Time.Get_Unix() - int(Reply))}");
        case "Trinity¤Heartbeat":
            Reply = Reply.split("¤");
            Log.Info(f"The Trinity Relay's Server is current at {Reply[0]}% CPU Usage, {(int(Reply[2]) - (int(Reply[1]))) // 2**30}/{int(Reply[2]) // 2**30}GiB of Memory Used.");
    return True;

Trinity_Client(Processor=Client_Processor, Shell=True);
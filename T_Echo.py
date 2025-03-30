# This file imports Trinity and runs an Echo Endpoint.
from Trinity import *;

# Example Processor
def Echo(Client: Trinity_Client, Command: str) -> bool:
    Client.Send(Command);
    return True;

# Example Routine Function
def Echo_Routine():
    while True:
        for Relay in Connected_Clients:
            if (not Relay.Connected):
                Connected_Clients.remove(Relay); # This causes issues I think
        Log.Info(f"We can broadcast shid. is nice. {Connected_Clients}");
        for Relay in Connected_Clients:
            Relay.Send("There is a Mika hidden in your walls.")
        time.sleep(16);

Trinity_Ignition(Processor=Echo, Routine=Echo_Routine, Type="Endpoint");
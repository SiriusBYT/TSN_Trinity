# This file imports Trinity and runs an Echo Endpoint.
from Trinity import *;

# Example Processor
def Echo(Client: Trinity_Socket, Command: str) -> bool:
    Client.Send(Command);
    return True;

# Example Routine Function
def Echo_Routine(Client: Trinity_Socket):
    time.sleep(10);
    while (Client.Connected):
        Client.Send(f"Routine Message!");
        time.sleep(10);

Trinity_Server(Processor=Echo, Routine=Echo_Routine, Type="Endpoint");
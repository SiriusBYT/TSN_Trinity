# This file imports Trinity and runs its client.
from TSN_Abstracter import *; Log.Clear();
from Trinity import *;

Trinity_Client(Address = ("localhost", 1407), Shell=True);
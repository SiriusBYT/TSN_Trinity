# This file imports Trinity and runs its client.
from Trinity import *;
import TSN_Abstracter;

Log.Clear();
Config.Logging["File"] = False; # Disable Log Files
Trinity_Client(Address = ("localhost", 1407), Shell=True);
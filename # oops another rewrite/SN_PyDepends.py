# Modules
import time # Required for sleep functions and time related shenanigans
import discord_webhook # I'm not fucking logging into SSH every nano second but I'm a chronically online Flashcord user so.. Discord for emergency notifications!!!
import configparser # Required for loading config files
import sys # For Crash() Function

# Load sensitive information
import dotenv, os
dotenv.load_dotenv()

SRV_Name = os.getenv('SRV_Name')
SRV_Desc = os.getenv('SRV_Desc')
SRV_Vers = os.getenv('SRV_Vers')

""" Sensitive Variables """
DWeb_LogURL = os.getenv("DWeb_LogURL") # Private
DWeb_PubURL = os.getenv("DWeb_PubURL") # Public


""" Variables for Webhooks Logging """
# Colors for Webhook Color
Color_Red = "FF3737"
Color_Orange = "FFE137"
Color_Green = "37FF64"
Color_Blue = "3764FF"
Color_Purple = "9B32FF"
Color_Pink = "FF9BFF"

# Keywords for getting Webhook Color
""" [!] This should be replaced by an external JSON file. """
Words_Error = [
    "ERROR",
    "SHUTDOWN",
    "CRASH",
    "FUCK",
    "OFFLINE"
]
Words_Warning = [
    "WARNING",
    "TIMED OUT"
]

Words_Success = [
    "SUCCESS",
    "OK",
    "ONLINE"
]
Words_Info = [
    "INFO",
    "REQUEST",
    "CONNECTION",
    "FORWARDING"
]
Words_Special = [
    "SYSTEM"
]

""" Private Functions """
# Used for Webhook Embeds 
def DWeb_Color(String):
    for cycle in Words_Error:
        if cycle in String:
            return Color_Red
    for cycle in Words_Warning:
        if cycle in String:
            return Color_Orange
    for cycle in Words_Success:
        if cycle in String:
            return Color_Green
    for cycle in Words_Info:
        if cycle in String:
            return Color_Blue
    for cycle in Words_Special:
        if cycle in String:
            return Color_Purple
        
    """ [!] This is kinda ugly, there has to be a better way to do this. 
    ADDITIONAL NOTICE: Use regex instead because sometimes words have punctuation glued to them which causes issues"""
    return Color_Pink

""" Logging Functions """
# Get current time string in the example format "22:10:10" - "31-07-2024"
def GetTime():
    CTime = time.localtime()
    Time = f"{CTime.tm_hour:02d}:{CTime.tm_min:02d}:{CTime.tm_sec:02d}"
    Date = f"{CTime.tm_mday:02d}-{CTime.tm_mon:02d}-{CTime.tm_year}"
    return Time,Date

def Log(Log):
    Log = str(Log) # Failsafe if this function is wrongly called, especially when debugging
    Time,Date = GetTime()
    TLog = f"[{Time}] {Log}"
    with open(f"logs/{Date}.log", "a", encoding="utf=8") as LogFile:
        LogFile.write(f"{TLog}\n")
        print(TLog)

    DWeb = discord_webhook.DiscordWebhook(url=DWeb_LogURL, rate_limit_retry=True)
    DWeb_Embed = discord_webhook.DiscordEmbed(title="", description=Log, color=DWeb_Color(Log))
    DWeb_Embed.set_footer(text=f"Log Time: {Time} - {Date}")
    DWeb.add_embed(DWeb_Embed)
    DWeb.execute()


""" int() Functions """
# Logs the server's basic information
def LoadCFG(CFG_File):
    CFG = configparser.ConfigParser()
    CFG.read(CFG_File)
    CFG.sections()
    Log(f'[System] Loaded configuration file "{CFG_File}".')
    return CFG

# Checks if a specified array number exist
# 04/10/24: This function is retarded! Just do "if [variable here]:"!!!
def doesEntryExists(Array,Number):
    try:
        Dummy = Array[Number]
        return True
    except:
        return False

""" void() Functions """

# Quickly send a Discord Webhook Embed Message
def DWeb_Send(Title, Description, Visibility):
    match Visibility:
        case "Private":
            URL = DWeb_LogURL
        case "Public":
            URL = DWeb_PubURL

    Time,Date = GetTime()
    DWeb = discord_webhook.DiscordWebhook(url=URL, rate_limit_retry=True)
    DWeb_Embed = discord_webhook.DiscordEmbed(title=Title, description=Description, color=DWeb_Color(f"{Title} {Description}"))
    DWeb_Embed.set_footer(text=f"Log Time: {Time} - {Date}")
    DWeb.add_embed(DWeb_Embed)
    DWeb.execute()

def Crash(Error, AllowRestart):
    Log(f"[CRASH] The server has crashed!")
    print(Error)
    DWeb_Send("⚠️ The server has crashed!", Error, "Private")
    if AllowRestart == True:
        for cycle in range (10):
            Log(f"Restarting server in {10-cycle}...")
            time.sleep(1)
    else:
        try: sys.exit(130)
        except SystemExit: os._exit(130)

def DoNothing(): return
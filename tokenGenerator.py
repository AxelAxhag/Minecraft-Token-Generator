import requests
import requests.utils
import sys
import os
import time
import urllib.parse
import re
from config import *


# Generates the bearer token for the minecraft API, the credentials are the same credentials used for logging into minecraft.net (migrated account).
# Enter also the amount of tokens to be generated
def generateToken(email, password, amount) -> None:
    if (tokensAreOld()):
        print('Refreshing old tokens...')
        filePath = os.path.dirname(__file__) + '/tokens'
        file = open(filePath, 'w')
        file.truncate()
        writeTokenTime()
        file.close()
    if (getTokenAmount() < 1):
        writeTokenTime()
    if (getTokenAmount() == amount):
        print(f'The Bearer tokens have been fully loaded! ({getTokenAmount()} tokens)')
        return()

    """ 
    SETUP
    """

    # The credentials need to be encoded in order to be properly understood by microsoft's server. These are sent by the microsoft body.
    emailEncode = urllib.parse.quote(email)
    passwordEncode = urllib.parse.quote(password)

    # Session is needed to store the cookies in order for the login to go over smoothly because microsoft needs cookies to authenticate 
    session = requests.Session()

    tagRequest = session.get('https://login.live.com/oauth20_authorize.srf?client_id=000000004C12AE6F&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en')

    # These are needed. urlPost got the URL to post the request to, the sFFTag I have no idea what it does
    try:
        sFFTag = re.search('value="(.+?)"', tagRequest.text).group(1)
        urlPost = re.search("urlPost:'(.+?)'", tagRequest.text).group(1)
    except:
        print('The sFFTag and/or the urlPost couldn\'t be fetched! Retrying...')
        if (tagRequest.status_code != 200):
            print(f'HTTP: {tagRequest.status_code}')
        time.sleep(60)
        generateToken(email, password, amount)
        return()

    sFFTagEncode = urllib.parse.quote(sFFTag)

    """
    MICROSOFT API 
    """

    # This header (somewhat similar to a body) is a json format in a dictionary-form which tells that the body is going to be in normal text format
    microsoftHeader = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Bodies can take whole lot of different forms; such as JSONs (dictionary-form) or general data such as a string in this example!
    microsoftBody = f'login={emailEncode}&loginfmt={emailEncode}&passwd={passwordEncode}&PPFT={sFFTagEncode}'

    # Actual request to microsoft to get their access token in order to get the bearer token from minecraft
    # The token is stored in the URL of signinRequestMicrosoft.url which has been sent through a multitude redirects
    signinRequestMicrosoft = session.post(urlPost, allow_redirects=True, data=microsoftBody, headers=microsoftHeader)

    if (signinRequestMicrosoft.text.find('Sign in to') != -1):
        print(f'Your credentials are wrong or you own a Mojang account!\nIf you\'re sure that you own a Microsoft then please check your credentials\nCredentials include your email and password.')
        return()
    
    if (signinRequestMicrosoft.text.find('Help us protect your account') != -1):
        print('Your account has 2 factor authentication (2FA) enabled! \nThis sniper unfortunately doesn\'t support it, in order for it to work you have to disable it.')
        return()

    try:
        # Handle all the data
        rawLoginData = signinRequestMicrosoft.url.split('#')[1]        # Entire URL which contains all the login info
        loginData = dict(item.split("=") for item in rawLoginData.split("&"))      
        loginData["access_token"] = requests.utils.unquote(loginData["access_token"])   # Decodes the access token
        loginData["refresh_token"] = requests.utils.unquote(loginData["refresh_token"])     # Decodes the refresh token
    except:
        print('The access token and/or refresh token couldn\'t be fetched! Retrying...')
        if (signinRequestMicrosoft.status_code != 200):
            print(f'HTTP: {signinRequestMicrosoft.status_code}')
        time.sleep(60)
        generateToken(email, password, amount)
        return()


    """ 
    XBOX LIVE API 
    """

    # Header for xbox live
    xboxHeader = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Body for xbox live
    xboxBody = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"{loginData['access_token']}" # you may need to add "d=" before the access token as mentioned earlier
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT"
    }

    # Request for xbox live
    signinRequestXbox = session.post('https://user.auth.xboxlive.com/user/authenticate', headers=xboxHeader, json=xboxBody)


    try:
        # Xbox live token
        xboxToken = signinRequestXbox.json()['Token']
        # Xbox live user hash
        xboxUserHash = signinRequestXbox.json()['DisplayClaims']['xui'][0]['uhs']
    except:
        print('The xbox token and/or xbox user hash couldn\'t be fetched! Retrying...')
        if (tagRequest.status_code != 200):
            print(f'HTTP: {signinRequestXbox.status_code}')
        time.sleep(60)
        generateToken(email, password, amount)
        return()

    """ 
    SEPERATE XBOX LIVE API 
    """

    # Xbox service header
    xstsHeader = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Xbox service body
    xstsBody = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [
                f"{xboxToken}"
            ]
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT"
    }

    # Request to the xbox service
    signinXSTS = session.post('https://xsts.auth.xboxlive.com/xsts/authorize', headers=xstsHeader, json=xstsBody) 

    try:
        # Token for the xbox service
        xstsToken = signinXSTS.json()['Token']
    except:
        print('The XSTS token couldn\'t be fetched! Retrying...')
        if (signinXSTS.status_code != 200):
            print(f'HTTP: {signinXSTS.status_code()}')
        time.sleep(60)
        generateToken(email, password, amount)
        return()

    """
    MINECRAFT API (ACTUAL API-KEY) 
    """

    # Minecraft Header
    minecraftHeader = {
        'Content-Type': 'application/json'
    }

    # Minecraft body
    minecraftBody = {
    "identityToken" : f"XBL3.0 x={xboxUserHash};{xstsToken}",
    "ensureLegacyEnabled" : 'true'
    }


    while (getTokenAmount() != amount):
        # Request to minecraft's servers in order to get the final token
        signinMinecraft = session.post('https://api.minecraftservices.com/authentication/login_with_xbox', headers=minecraftHeader, json=minecraftBody)

        # Closing the session so to not overwrite other sessions
        session.close()

        try:
            # The actual token for authenticating actions on the minecraft API
            bearerToken = f'{signinMinecraft.json()["token_type"]} {signinMinecraft.json()["access_token"]}'
        except:
            print('The bearer token couldn\'t be fetched! Retrying...')
            if (signinMinecraft.status_code != 200):
                print(f'HTTP: {signinMinecraft.status_code}')
            time.sleep(60)
            generateToken(email, password, amount)
            return()

        filePath = os.path.dirname(__file__) + '/tokens'

        tokenFile = open(filePath, 'a')
        tokenFile.write(f'{bearerToken}\n')
        tokenFile.close()
        
        print(f'({getTokenAmount()}/{amount}) Bearer tokens loaded!')
        
        if (getTokenAmount() != amount):
            time.sleep(5)


def getTokenAmount() -> int:
    try:
        filePath = os.path.dirname(__file__) + '/tokens'
        file = open(filePath, 'r')
        amount = (len(file.read().split('\n'))) - 2
        file.close()
    except:
        return(0)

    return(amount)

def tokensAreOld() -> bool:
    try: 
        filePath = os.path.dirname(__file__) + '/tokens'
        file = open(filePath, 'r')
        lastTime = int(file.read().split('\n')[0])
        file.close()
        if ((int(time.time()) - lastTime) > (60*60*24)):
            return(True)
    except:
        return(False)
    
def writeTokenTime() -> None:
    filePath = os.path.dirname(__file__) + '/tokens'
    file = open(filePath, 'w')
    file.write(str(int(time.time())) + '\n')
    file.close()

def containsDuplicate(tokenList) -> bool:
    newSet = set(tokenList)
    if (len(newSet) != len(tokenList)):
        return True
    return False

def yes() -> bool:
    answer = input().lower()
    if (answer == 'y'):
        return True
    if (answer == 'n'):
        return False
    else: 
        print('Please input a valid answer, type \'y\' or \'n\'')
        yes()

def getTokens(email, password, amount) -> list:
    generateToken(email, password, amount)
    filePath = os.path.dirname(__file__) + '/tokens'
    file = open(filePath, 'r')
    tokenList = file.read().split('\n')
    tokenList.pop(0)
    tokenList.pop()
    if (containsDuplicate(tokenList)):
        print('There is at least 1 duplicate token! \nDo you want to refresh the tokens? (y/n)')
        if(yes()):
            getTokens(email, password, amount)
    return(tokenList)


# Main function
def main(): 
    generateToken(email, password, amount)
  
if __name__=="__main__": 
    main() 
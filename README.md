# Minecraft Token Generator 

## What is it? 🔑

This script automates the process of gathering a specified amount of unique bearer tokens for a minecraft account. These can be used to change your profile using the minecraft API.

## What is a token used for? 🤔

As previously stated, the tokens are used to interact with the minecraft API. The tokens are a means of authenticating who you are. The limits of what can be done with the tokens are set by the minecraft API itself. Let's say however that you want to 'snipe'. Sniping is a process where you seek to acquire a sought after username. Some usernames that are no longer in use get released to the public, however, if the demand is high then it can become hard to acquire it since people automate the process of changing their previous username to the new one using bots. In order to automate the process you need to have a way of authenticating yourself, this is done through tokens. This can't be done (at least to my knowledge) by simply sending your credentials over to the minecraft API. You need to have a token/tokens to automate any process using the minecraft API.    

## General questions ❓

* Why do you check generate multiple tokens? - The reason why is because for some API calls (such as name changing), mojang has set a limit for how many calls you can make during a certain time period.
* Does this work for my account? - It only works for migrated accounts that have transitioned to Microsoft. If you login through the Microsoft login page then you have a migrated account and you're able to generate tokens. If you're using a Mojang account then this won't work.
* For how long do my tokens last? - They last for 24h, I believe, after that time has passed the tokens have to be refreshed/regenerated. This is handled by the program, removing the old ones and creating new ones.
* Why would I need multiple tokens? - The reason why is because Mojang limits the amount your amount of traffic based on your token. You can skirt by this restriction by using multiple tokens. Don't think you have to use proxies, however it might be wise to use some if you were to send that much traffic.

## How to get it running 🚗

1. Go into the config.py file to change the credentials to your minecraft account
2. Execute the tokenGenerator.py file
3. Wait until the tokens are generated (Status is printed in the console)
4. Then there should be a file in the same folder named tokens containing all of the tokens

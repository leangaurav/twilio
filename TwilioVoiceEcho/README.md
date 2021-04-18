# Twilio Voice Echo

This project allows you to run a simple **voice echo** system on you Twilio virtual number.
It is based on twilio voice bi-directional streams which allows you to direct a call to a websocket server.

The project contains code to handle the websocket as well as the Twiml request. So you need not  create a separate twiml bin.
All you need is to point your phone number to the correct endpoint which is described in detail later.

One additional point to note is that twilio only allows secure websockets or sockets over wss protocol and  or that we are using `ngrok`.
`ngrok` is available for all platforms. Make sure you have that installed on your system before trying this out.

The  call will run for a maximum of 30 seconds after the bot's message finished, due to a default max call setting. See .env file to increase the limit or remove it altogether.

The project can be run either using one of the below options:
- docker and docker compose
- directly with python


## Using Docker and docker-compose

#### Step-1: Running the server
This is the easiest method. You just need to open .env and set the correct environment variables for the TwilioVoiceEcho section.
before that make sure you have ngrok and you have started an http tunnel via the command

  `ngrok http 8000`
  
Here you can you any other port as well. whatever port you use, you need to update the same in .env
![image](https://user-images.githubusercontent.com/35618518/115155093-f5d9d180-a09b-11eb-9c11-d2cd2e05b014.png)

After running, you will see something like  what is  in above screenshot. From there you need to copy the `Forwardding` url.
Which in this case is `https://a74c7c5ee5aa.ngrok.io`. We need to use it in a couple of places.

Now open your `.env` file and based based on above values, it should look like this.

```
###################
# TwilioVoiceEcho #
###################

BIND_ADDRESS=0.0.0.0:8000

# HOST_ADDRESS should have wss protocol
WS_ADDRESS=wss://a74c7c5ee5aa.ngrok.io

# The call will disconnect after this time. set to -1 to disable
MAX_CALL_DURATION=30
```

The port in BIND_ADDRESS should match the one you used in `ngrok` command.
Also notice the `wss://`. Thats the websocket address with https replaced with wss.

After saving `.env`, you just need to run the container:

`docker-compose up --build TwilioVoiceEcho`

  or for detached mode use
  
`docker-compose up --build -d TwilioVoiceEcho`

#### Step-2: Setting up your twilio voice number

If you don't have a twilio account, then create a free twilio account.
Once signup is complete, then you need to go to the phone numbers section to buy a number or open an already purchased phone number.
Open the settings for that phone number.

![image](https://user-images.githubusercontent.com/35618518/115155441-9e3c6580-a09d-11eb-8688-64d2dd27a955.png)

Make sure you have your  `Accept Incoming`, `Configure With` and `A Call Come In` sections look like what's above.
Notice the webhook value, it is the same ngrok url suffixed with `/twiml`.
Make sure you replace it with the URL that ngrok gave it to you and suffix it with /twiml
Remember to save this.

Now all you need to do is call your  virtual nexmo number, and after the `this is an echo bot` completes, whatever you say will be echoed.
  
  
## Directly with python

#### Step-1
Make sure you have python 3.4+ installed for all things to work.
Create a virtual environment for running this

`python -m venv venv`

Activate this  virtual env and install the requirements present under TwilioVoiceEcho/requirements.txt
Run ngrok tunnel
`ngrok http 8000`

Then run this command replacing the relevant values for  `bind_address` port, the `ngrok` url in ws_host
` python -m TwilioVoiceEcho.app.main --bind_address 0.0.0.0:8000 --ws_host wss://localhost.ngrok.io --max_call_time 30`
 
 #### Step-2
 This is same as for docker setup

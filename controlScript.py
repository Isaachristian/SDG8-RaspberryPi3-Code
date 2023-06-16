#!/usr/bin/python3

# IMPORTS
from datetime import datetime
from enum import Enum
import serial
import logging
import os
import subprocess

import time



# CONSTANTS
LOG_FOLDER = "logs"
PRESETS_FOLDER = "presets"
PHOTO_CAPTURE_FOLDER = "captures"
USB_PORT = "/dev/ttyACM0"  # USB Port Location



# ENUMS
class USB(Enum): # (A = Sent by ATmega, P = Sent by Pi)
  EMPTY_USB_BUF = b''

  # Boot
  P_BOOT_DONE = b'boot_done'

  # Connection
  A_GET_PAST_IP = b'get_past_ip'
  P_RETURN_PAST_IP = b'past_ip='
  A_TRY_CONNECT = b'ip='
  P_CONNECTION_GOOD = b'connection_good'
  P_CONNECTION_BAD = b'connection_bad'
  
  # Retrieving Saved Presets
  A_GET_PRESETS = b'get_presets'
  P_PRESETS = b'presets='

  # Save New Preset
  A_SAVE_PRESET = b'save_preset='
  P_SAVE_PRESET_DONE = b'save_preset_done'

  # Camera
  A_CAPTURE_IMG = b'capture_image'
  P_CAPTURE_IMAGE_DONE = b'capture_image_done'

  # Uploading Images
  A_STRT_UPLOAD = b'begin_upload'
  P_FINISH_UPLOAD = b'finish_upload'



# BEGIN LOGGING
if not os.path.exists('logs'):
  os.makedirs('logs')

filename = f'{LOG_FOLDER}/debug.log' # -{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG)
logging.info("Starting program...")



# CREATE NEEDED FOLDERS
if not os.path.exists(PRESETS_FOLDER):
  logging.info("Creating presets folder...")
  os.makedirs(PRESETS_FOLDER)

if not os.path.exists(PHOTO_CAPTURE_FOLDER):
  logging.info("Creating photo capture folder...")
  os.makedirs(PHOTO_CAPTURE_FOLDER)



# ATTEMPT INITIAL USB CONNECTION
try:
  logging.info(f"Attemtping to connect to usb at {USB_PORT}")
  usb = serial.Serial(USB_PORT, 9600, timeout = 10)
except:
  logging.error("Could not open USB serial port; check your port name and permissions.")
  logging.error("Exiting program...")
  exit()
else:
  logging.info("Connected to USB")



# INFORM ATMEGA BOOT SEQUENCE IS COMPLETED
logging.info("Sending BOOT_DONE to ATMEGA...")
usb.write(USB.P_BOOT_DONE.value)



# FUNCTIONS
def check(command: str, startsWith: bool, USBValue):
  return command == USBValue.value or (startsWith and command.startswith(USBValue.value))

def getPastIP():
  logging.info("Retreiving previous IP address...")
  try: 
    ipFile = open('ip.data', 'r', encoding='utf-8')
    ip = ipFile.readline().strip()
    logging.info(f"Returning {ip}...")
    usb.write(f'{USB.P_RETURN_PAST_IP.value}{ip}')
  except:
    logging.info(f"No IP saved; returning 0.0.0.0...")
    usb.write(f'{USB.P_RETURN_PAST_IP.value}0.0.0.0')

def tryConnection(commandStr):
  ip = commandStr.split("=")[1]
  logging.info(f'Attempting to connect to <{ip}>...')
  
  # Attempt a connection to the workstation software
  time.sleep(5) # ...simulate connection timing

  # If successful log and write success to USB, else return bad
  if True:
    logging.info(f'Connection to <{ip}> successful...')

    try:
      logging.info(f'Writing IP to file...')
      IPFile = open("ip.data", 'w', encoding="utf-8")
      IPFile.write(f'{ip}\n')
    except:
      logging.error("Failed to write IP to file")
    finally:
      IPFile.close()

    usb.write(USB.P_CONNECTION_GOOD.value)
  else:
    logging.info(f'Connection to <{ip}> unsuccessful...') # TODO: maybe show error messages?
    usb.write(USB.P_CONNECTION_BAD.value)

def writePresetToFile(commandStr: str):
  preset = commandStr.split('=')[1]
  logging.info(f"Attempting to save '{preset}'")

  try:
    logging.info(f"Attempting to open 'presets.data'...")
    presetsF = open("presets/presets.data", 'a', encoding="utf-8")

    try:
      logging.info(f"Attempting to write '{preset}' in 'presets.data'...")
      presetsF.write(f'{preset}\n')
    except:
      logging.error("Could not write to 'presets.data'!")
    finally:
      logging.info("Closing the file...")
      presetsF.close()

  except:
    logging.error("Could not open 'presets.data'!")
  finally:
    # usb.write(USB.P_SAVE_PRESET_DONE.value)
    logging.info("Preset written to file")

def getPresets():
  try:
    logging.info("Opening 'presets.data'...")
    presetsFile = open('presets/presets.data', 'r', encoding='utf-8')

    try:
      logging.info("Reading 'presets.data'...")
      presetsFileContent = presetsFile.read()
    except:
      logging.error("Could not read presets")
    finally:
      presetsFile.close()
      
    presetData = ''

    logging.info("Processing 'presets.data'...")
    presets = presetsFileContent.splitlines()
    if len(presets) > 0:
      presets.reverse()
    
      presetData = presets.pop(0)
      for p in presets:
        presetData += f';{p}'
    
    # TODO serial write presets
    usb.write(f'{USB.P_PRESETS.value}{"presetStr"}')
    logging.info('Presets written to buffer...')

  except:
    logging.error("Could not open 'presets.data'")

def captureImage(imgFolder: str, imgIdx: int) -> tuple[str, int]:
  logging.info('Capturing image...')

  if (imgFolder == ''):
    logging.info("Creating target folder...")
    imgFolder = f'{PHOTO_CAPTURE_FOLDER}/{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    imgIdx = 0
    try:
      os.makedirs(imgFolder)
    except:
      logging.error(f'Failed to create the target folder: {imgFolder}')

  logging.info(f"Running gphoto2; Placing image {imgIdx} into folder '{imgFolder}'...")
  _, error = subprocess.Popen(
    f"cd {imgFolder} && gphoto2 --filename={imgIdx}.jpeg --capture-image-and-download",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  ).communicate()

  if error.decode('utf-8') == '':   # output = output.decode("utf-8")
    logging.info('Photo captured successfully...')
  else:
    logging.error(f'gPhoto2 returned the following error(s):\n\n{error}\n')

  return [imgFolder, imgIdx + 1]

def startUpload(commandStr):
  print(commandStr)

# ENTER MAIN CONTROL SCRIPT
# command = b'ip=192.168.1.100'.strip() # usb.readline().strip()
# command = b'save_preset=4,4,50,20'.strip() # usb.readline().strip()
# command = USB.A_GET_PRESETS.value # usb.readline().strip()
command = USB.A_CAPTURE_IMG.value # usb.readline().strip()
commandStr = command.decode()

imgFolder: str = ''
imgIdx = 0
while True:
  if   check(command, False, USB.EMPTY_USB_BUF): continue
  elif check(command, True,  USB.A_GET_PAST_IP): getPastIP()
  elif check(command, True,  USB.A_TRY_CONNECT): tryConnection(commandStr)
  elif check(command, False, USB.A_GET_PRESETS): getPresets()
  elif check(command, True,  USB.A_SAVE_PRESET): writePresetToFile(commandStr)
  elif check(command, False, USB.A_CAPTURE_IMG): imgFolder, imgIdx = captureImage(imgFolder, imgIdx)
  elif check(command, False, USB.A_STRT_UPLOAD): imgFolder = startUpload(imgFolder)
  else: logging.error(f'Unknown command: {command}')

  print(imgFolder)

  logging.info("Listening for command...")

  # **DEBUG! REMOVE**
  command = USB.EMPTY_USB_BUF.value
  commandStr = command.decode()


#!/usr/bin/python3

# IMPORTS
from datetime import datetime
from enum import Enum
# import serial
import logging
import os



# CONSTANTS
LOG_FOLDER = "logs"
PRESETS_FOLDER = "presets"
USB_PORT = "/dev/ttyACM0"  # USB Port Location



# ENUMS
class USB(Enum): # (A = Sent by ATmega, P = Sent by Pi)
  EMPTY_USB_BUF = b''

  # Boot
  P_BOOT_DONE = b'boot_done'

  # Connection
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



# CREATE LOG FOLDER IF IT DOESN'T EXIST
if not os.path.exists('logs'):
  os.makedirs('logs')



# INIT LOGGING
filename = f'{LOG_FOLDER}/debug.log' # -{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG)
logging.info("Starting program...")



# CREATE PRESETS FOLDER IF IT DOESN'T EXIST
if not os.path.exists(PRESETS_FOLDER):
  logging.info("Creating presets folder...")
  os.makedirs(PRESETS_FOLDER)



# ATTEMPT INITIAL USB CONNECTION
try:
  logging.info(f"Attemtping to connect to usb at {USB_PORT}")
  # usb = serial.Serial(USB_PORT, 9600, timeout = 10)
except:
  logging.error("Could not open USB serial port; check your port name and permissions.")
  logging.error("Exiting program...")
  exit()
else:
  logging.info("Connected to USB")



# INFORM ATMEGA BOOT SEQUENCE IS COMPLETED
logging.info("Sending BOOT_DONE to ATMEGA...")
# usb.write(USB.P_BOOT_DONE)



# FUNCTIONS
def check(command: str, startsWith: bool, USBValue):
  return command == USBValue.value or (startsWith and command.startswith(USBValue.value))

def tryConnection(commandStr):
  ip = commandStr.split("=")[1]
  logging.info(f'Attempting to connect to <{ip}>...')
  

  # Attempt a connection to the workstation software
  # ...

  # If successful log and write success to USB, else return bad
  # if True:
  #   serial.Write(USB.P_CONNECTION_GOOD)
  # else:
  #   serial.Write(USB.P_CONNECTION_BAD)

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
    print()
    # usb.write(USB.P_SAVE_PRESET_DONE)

def getPresets(commandStr: str):

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
      
    presetStr = ''

    logging.info("Processing 'presets.data'...")
    presets = presetsFileContent.splitlines()
    if len(presets) > 0:
      presets.reverse()
    
      presetStr = presets.pop(0)
      for p in presets:
        presetStr += f';{p}'
    
    # TODO serial write presets
    # usb.write(f'{USB.P_PRESETS.value}{presetStr}')

  except:
    logging.error("Could not open 'presets.data'")


  print(commandStr)

def captureImage(commandStr):
  print(commandStr)

def startUpload(commandStr):
  print(commandStr)

# ENTER MAIN CONTROL SCRIPT
# command = b'ip=192.168.1.100'.strip() # usb.readline().strip()
# command = b'save_preset=4,4,50,20'.strip() # usb.readline().strip()
command = USB.A_GET_PRESETS.value # usb.readline().strip()
commandStr = command.decode()
while True:
  if   check(command, False, USB.EMPTY_USB_BUF): continue
  elif check(command, True,  USB.A_TRY_CONNECT): tryConnection(commandStr)
  elif check(command, False, USB.A_GET_PRESETS): getPresets(commandStr)
  elif check(command, True,  USB.A_SAVE_PRESET): writePresetToFile(commandStr)
  elif check(command, False, USB.A_CAPTURE_IMG): captureImage(commandStr)
  elif check(command, False, USB.A_STRT_UPLOAD): startUpload(commandStr)
  else: logging.error(f'Unknown command: {command}')

  # **DEBUG! REMOVE**
  command = USB.EMPTY_USB_BUF.value
  commandStr = command.decode()


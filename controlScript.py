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
  A_CAPTURE_IMAGE = b'capture_image'
  P_CAPTURE_IMAGE_DONE = b'capture_image_done'

  # Uploading Images
  A_BEGIN_UPLOAD = b'begin_upload'
  P_FINISH_UPLOAD = b'finish_upload'



# CREATE LOG FOLDER IF IT DOESN'T EXIST
if not os.path.exists('logs'):
  os.makedirs('logs')



# INIT LOGGING
filename = f'{LOG_FOLDER}/debug-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=filename, level=logging.DEBUG)
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
def check(command: str, USBValue):
  print(USBValue.value)
  print(command == USBValue.value or command.startswith(USBValue.value))
  return command == USBValue.value or command.startswith(USBValue.value)

def tryConnection(commandStr):
  ip = commandStr.split("=")[1]
  logging.info(f'Attempting to connect to <{ip}>...')
  print(ip)

  # Attempt a connection to the workstation software
    # If successful log and write success to USB
    # Else, do the opposite

def writePresetToFile(commandStr):
  preset = commandStr.split('=')[1]
  logging.info(f"Attempting to save '{preset}'")

  try:
    logging.info(f"Attempting to open 'presets.data'...")
    presetsF = open("presets/presets.data", 'w', encoding="utf-8")

    try:
      logging.info(f"Attempting to write {preset} 'presets.data'...")
      presetsF.write(preset)
      presetsF.close()
    except:
      logging.error("Could not write to 'presets.data'!")

  except:
    logging.error("Could not open 'presets.data'!")




# ENTER MAIN CONTROL SCRIPT
# command = b'ip=192.168.1.100'.strip() # usb.readline().strip()
command = b'save_preset=4,4,50,20'.strip() # usb.readline().strip()
commandStr = command.decode()
while True:
  if   check(command, USB.EMPTY_USB_BUF): continue
  elif check(command, USB.A_TRY_CONNECT): tryConnection(commandStr)
  elif check(command, USB.A_GET_PRESETS): print(command)
  elif check(command, USB.A_SAVE_PRESET): writePresetToFile(commandStr)
  elif check(command, USB.A_GET_PRESETS): print(command)
  elif check(command, USB.A_GET_PRESETS): print(command)
  else: logging.error(f'Cound not identify command: {command}')

  # **DEBUG! REMOVE**
  command = USB.EMPTY_USB_BUF.value
  commandStr = command.decode()


#!/usr/bin/python3

# IMPORTS
from datetime import datetime
from enum import Enum
import serial
import logging
import os



# CONSTANTS
USB_PORT = "/dev/ttyACM0"  # USB Port Location



# ENUMS
class USB(Enum): # (A = Sent by ATmega, P = Sent by Pi)
  # Boot
  P_BOOT_DONE = b'boot_done'

  # Connection
  A_TRY_CONNECTION = b'ip='
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




# CREATE LOG FOLDER
if not os.path.exists('logs'):
  os.makedirs('logs')



# INIT LOGGING
filename = f'logs/debug-{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename, level=logging.DEBUG)
logging.info("Starting program...")



# ATTEMPT INITIAL USB CONNECTION
try:
  logging.info(f"Attemtping to connect to usb at {USB_PORT}")
  usb = serial.Serial(USB_PORT, 9600, timeout = 10)
except:
  logging.debug("ERROR: Could not open USB serial port; check your port name and permissions.")
  logging.info("Exiting program...")
  exit()
else:
  logging.info("Connected to USB")



# INFORM ATMEGA BOOT SEQUENCE IS COMPLETED
logging.info("Sending BOOT_DONE to ATMEGA...")
usb.write(USB.BOOT_DONE)



# ENTER MAIN CONTROL SCRIPT
# while True:
#   if 

import logging
import os
import subprocess
import sys
import time
import serial
import serial.tools.list_ports

# Project Imports
from utils.USB import USB
from utils.constants import *


# Functions
def setupLogging(): 
  """Initialize the Logging for Debug"""

  if not os.path.exists('logs'):
    os.makedirs('logs')

  filename = f'{LOG_FOLDER}/debug.log' # -{datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
  logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG)
  logging.info("Starting program...\n")


def createFolders():
  """Creates folders for presets and captures if they are not present"""

  if not os.path.exists(PRESETS_FOLDER):
    logging.info("Creating presets folder...")
    os.makedirs(PRESETS_FOLDER)

  if not os.path.exists(PHOTO_CAPTURE_FOLDER):
    logging.info("Creating photo capture folder...\n")
    os.makedirs(PHOTO_CAPTURE_FOLDER)


def checkCameraConnection():
  """Attempts to connect to the Camera. If no camera is detected, it will recursively call itself 
  every 5 seconds until on is detected."""

  if len(sys.argv) > 1 and sys.argv[1] == '1':
    logging.info("Check for camera skipped!\n")
    return

  gPhoto2out, gPhoto2Err = subprocess.Popen(
    "gphoto2 --auto-detect",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  ).communicate()

  cam = gPhoto2out.decode('utf-8').splitlines()
  if len(cam) > 2 or gPhoto2Err.decode('utf-8') != '':
    logging.info(f"Connected to: {cam[2]}")
  else:
    logging.error(f"Could not find camera!\n\n{gPhoto2out.decode('utf-8')}")
    logging.info("Checking again in 5 seconds...\n\n")
    time.sleep(5)

    checkCameraConnection()


def findArduino() -> str:
  """Automatically Finds Arduino"""
  
  if len(sys.argv) > 1 and sys.argv[1] == '1':
    pid = 67
    vid = 9025
  else:
    pid = 60001
    vid = 4292

  ports = serial.tools.list_ports.comports()
  for port in ports:
    if port.vid == vid and port.pid == pid: # ATmega2560 won't be Arduino
      return port.device

  return None


def connectToATmega():
  """Establishes serial communication over the specified USB port and waits for Arduino to reboot 
  (the connection process causes the ATmega to reboot)"""

  try:
    atmegaLocation = findArduino()

    logging.info(f"Attemtping to connect to USB at {atmegaLocation}")
    usb = serial.Serial(atmegaLocation, 9600)

    logging.info("Waiting for ATmega to boot...")

    while True: 
      test = usb.readline().decode('utf-8', 'ignore').strip()
      if (USB.A_BOOT_DONE.value.strip() in test): 
        break
      else: 
        print(test)

    logging.info("Arduino booted and connection established!\n")

    return usb
  except Exception as e:
    logging.error(f"Could not open USB serial port; check your port name and permissions.\n\n{e}\n")
    logging.error("Exiting program...")
    exit()


def sendPreviousIP(usb: serial.Serial):
  """Sent past IP to the ATmega as a response to boot"""
  logging.info("Retreiving previous IP address...")

  try: 
    ipFile = open('ip.data', 'r', encoding='utf-8')
    ip = ipFile.readline().strip()
    logging.info(f"Returning '{USB.P_RETURN_PAST_IP.value}{ip}'...\n")
    usb.write(f'{USB.P_RETURN_PAST_IP.value}{ip}\n'.encode())
  except:
    logging.info(f"No IP saved; returning '000000000000'...\n")
    usb.write(f'{USB.P_RETURN_PAST_IP.value}000000000000\n'.encode())


def init() -> serial.Serial:
  """Initiates logging, creates necessary folders, checks the connection to the camera,
     connects to the ATmega, sends the previously used IP to the ATmega, and return the
     USB connection"""

  setupLogging()
  createFolders()
  checkCameraConnection()
  usb = connectToATmega()
  sendPreviousIP(usb)

  return usb
#!/usr/bin/python3

# IMPORTS
from datetime import datetime
from enum import Enum
import serial
import serial.tools.list_ports
import logging
import os
import subprocess
import time
import socket
import zipfile
import sys



# CONSTANTS
LOG_FOLDER = "logs"
PRESETS_FOLDER = "presets"
PHOTO_CAPTURE_FOLDER = "captures"
DEFAULT_PORT = 25000
ACK_CONNECTION = b'ack_connection'



# ENUMS
class USB(Enum): # (A = Sent by ATmega, P = Sent by Pi)
  # Boot
  A_BOOT_DONE = 'boot_done'
  P_RETURN_PAST_IP = 'past_ip='

  # Connection
  A_TRY_CONNECT = 'ip='
  P_CONNECTION_GOOD = 'connection_good\n'
  P_CONNECTION_BAD = 'connection_bad\n'
  
  # Retrieving Saved Presets
  A_GET_PRESETS = 'get_presets'
  P_PRESETS = 'presets='

  # Save New Preset
  A_SAVE_PRESET = 'save_preset='
  P_SAVE_PRESET_DONE = 'save_preset_done'

  # Camera
  A_CAPTURE_IMG = 'capture_image'
  P_CAPTURE_IMAGE_DONE = 'capture_image_done'

  # Uploading Images
  A_STRT_UPLOAD = 'begin_upload'
  P_FINISH_UPLOAD = 'finish_upload'

  # Say Hi
  A_SAY_HELLO = 'say_hello'
  P_SAY_HELLO = 'say_hello_back'

  # End Program
  A_END_PROGRAM = 'end'



# INIT FUNCTIONS
def initLogging(): 
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
  ports = serial.tools.list_ports.comports()
  for port in ports:
    if 'Arduino' in port.manufacturer: # ATmega2560 won't be Arduino
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


def sendPreviousIP():
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



# GENERAL FUNCTIONS
def check(command: str, startsWith: bool, USBValue: str):
  """Check if the command is """
  return command == USBValue or (startsWith and command.startswith(USBValue))


def parseIP(ip: str):
  """IPs are being stored as 12 digit strings, this parses them into proper IP"""
  logging.info(f'Attempting to parse {ip}')
  return f'{int(ip[0:3])}.{int(ip[3:6])}.{int(ip[6:9])}.{int(ip[9:12])}'


def tryConnection(command: str, usb: serial.Serial):
  """Attempts to connect to the workstation. Expects to recieve an acknowledgement"""

  try:
    ip = parseIP(command.split("=")[1])
  except:
    logging.error('Failed to parse sent string!\n')
    usb.write(USB.P_CONNECTION_BAD.value.encode())
    return

  logging.info(f'Attempting to connect to <{ip}>...')
  
  # Attempt a connection to the workstation software
  connectionSuccessful = False
  try:
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpSocket.connect((ip, DEFAULT_PORT))

    data = tcpSocket.recv(1024)

    logging.info(f'Recieved {data.decode()} from server')

    if data == ACK_CONNECTION:
      connectionSuccessful = True

  except Exception as e:
    logging.error(f'Failed to connect to workstation: \n\n{e}\n')
    usb.write(USB.P_CONNECTION_BAD.value.encode())

  # If successful log and write success to USB, else return bad
  if connectionSuccessful:
    logging.info(f'Connection to <{ip}> successful...')

    try:
      logging.info(f'Writing IP to file...\n')
      IPFile = open("ip.data", 'w', encoding="utf-8")

      # write the ip as it was sent (unparsed)
      IPFile.write(f'{command.split("=")[1]}\n')
    except:
      logging.error("Failed to write IP to file\n")
    finally:
      IPFile.close()

    usb.write(USB.P_CONNECTION_GOOD.value.encode())

  return tcpSocket


def writePresetToFile(commandStr: str):
  """Writes a preset to storage"""

  # Get preset to save
  preset = commandStr.split('=')[1]
  logging.info(f"Attempting to save '{preset}'")

  try:
    logging.info(f"Attempting to open 'presets.data'...")
    presetsF = open("presets/presets.data", 'a', encoding="utf-8")

    try:
      logging.info(f"Attempting to write '{preset}' in 'presets.data'...")
      presetsF.write(f'{preset}\n')

    except:
      logging.error("Could not write to 'presets.data'!\n")

    finally:
      logging.info("Closing the file...")
      presetsF.close()

  except:
    logging.error("Could not open 'presets.data'!")
    usb.write(USB.P_SAVE_PRESET_DONE.value.encode())

  finally:
    logging.info("Preset written to file!\n")
    usb.write(USB.P_SAVE_PRESET_DONE.value.encode())


def getPresets():
  """Sends the latest 4 presets seperated by ';' over USB. Can return 0 to 4 results."""

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
      
    logging.info("Processing 'presets.data'...")
    presets = presetsFileContent.splitlines()
    if len(presets) > 0:
      presets.reverse()
    
      logging.info('Writing presets to buffer...\n')
      usb.write(f'{USB.P_PRESETS.value}{presets[0]}'.encode())

  except:
    logging.error("Could not open 'presets.data'")
    usb.write(USB.P_PRESETS.value.encode())


def captureImage(imgFolder: str, imgIdx: int, usb: serial.Serial) -> tuple[str, int]:
  """Captures an image and places it in in the image folder (creates if it doesn't exist); 
     Returns folder location and image index"""

  logging.info('Capturing image...')

  if (imgFolder == ''):
    logging.info("Creating target folder...")
    imgFolder = f'{PHOTO_CAPTURE_FOLDER}/{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    imgIdx = 0

    try:
      os.makedirs(imgFolder)

    except:
      logging.error(f'Failed to create the target folder: {imgFolder}')


  if len(sys.argv) > 1 and sys.argv[1] == '1':
    logging.info(f"Running libcam; Placing image {imgIdx} into folder '{imgFolder}'...")
    _, error = subprocess.Popen(
      f"cd {imgFolder} && libcamera-jpeg -o {imgIdx}.jpeg",
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE
    ).communicate()
  else:
    logging.info(f"Running gphoto2; Placing image {imgIdx} into folder '{imgFolder}'...")
    _, error = subprocess.Popen(
      f"cd {imgFolder} && gphoto2 --filename={imgIdx}.jpeg --capture-image-and-download",
      shell=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE
    ).communicate()

  if error.decode('utf-8') == '':
    logging.info('Photo captured successfully...')
  else:
    logging.error(f'Camera utility returned the following error(s):\n\n{error}\n')

  usb.write(f'{USB.P_CAPTURE_IMAGE_DONE.value}\n'.encode())

  return [imgFolder, imgIdx + 1]


def send_file(filename: str, conn: socket.socket):
  logging.info(f"Sending file to workstation")

  with open(filename, 'rb') as f:
    while True:
      data = f.read(1024)
      if not data:
        break

      conn.sendall(data)

  logging.info(f"File sent to workstation\n")


# def zip_file(images_dir, filename):
#   with zipfile.ZipFile(filename, 'w') as zipf:
#     for root, dirs, files in os.walk(images_dir):
#       for file in files:
#         zipf.write(os.path.join(root, file))

def zipdir(path):
  logging.info(f"Zipping directory at '{path}...'")

  # ziph is zipfile handle
  ziph = zipfile.ZipFile('photos.zip', 'w', zipfile.ZIP_DEFLATED)

  for root, dirs, files in os.walk(path):
    for file in files:
      ziph.write(
        os.path.join(root, file), 
        os.path.relpath(
          os.path.join(root, file), 
          os.path.join(path, '..')
        )
      )

  logging.info(f"Done zipping directory...")    
  ziph.close()

  return 'photos.zip'


def startUpload(imgFolder: str, tcpSocket: socket.socket):
  logging.info("Starting upload...")
  send_file(
    zipdir(f'{imgFolder}'), 
    tcpSocket
  )



# STARTUP
initLogging()
createFolders()
checkCameraConnection() # SKIPPED FOR TESTING
usb = connectToATmega()
sendPreviousIP()



# ENTER MAIN CONTROL SCRIPT
imgFolder: str = ''
imgIdx = 0
tcpSocket: socket
while True:
  logging.info("Listening for command...")
  
  command = usb.readline().strip().decode()

  if check(command, True,  USB.A_TRY_CONNECT.value): 
    tcpSocket = tryConnection(command, usb)
    
  elif check(command, False, USB.A_GET_PRESETS.value): 
    getPresets()

  elif check(command, True,  USB.A_SAVE_PRESET.value): 
    writePresetToFile(command)
  
  elif check(command, False, USB.A_CAPTURE_IMG.value): 
    imgFolder, imgIdx = captureImage(imgFolder, imgIdx, usb)
  
  elif check(command, False, USB.A_STRT_UPLOAD.value): 
    imgFolder = startUpload(imgFolder, tcpSocket)

  elif check(command, False, USB.A_END_PROGRAM.value):
    logging.info("Gracefully exiting per request by ATmega...")
    exit()
  
  else: 
    logging.error(f'Unknown command: {command}\n')

  usb.reset_input_buffer()


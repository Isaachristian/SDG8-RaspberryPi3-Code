import serial
import socket
import subprocess
import sys
from datetime import datetime

# Project Imports
from utils.utils import *
from utils.USB import *
from utils.constants import *



def tryConnection(command: str, usb: serial.Serial):
  """Attempts to connect to the workstation. Expects to recieve an acknowledgement"""

  try:
    ip = parseIP(command.split("=")[1])
  except:
    logging.error(f'Failed to parse sent string: \'{command}\'!\n')
    usb.write(USB.P_CONNECTION_BAD.value.encode())
    return

  logging.info(f'Attempting to connect to <{ip}>...')
  
  # Attempt a connection to the workstation software
  connectionSuccessful = False
  try:
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpSocket.settimeout(5)
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

def writePresetToFile(commandStr: str, usb: serial.Serial):
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


def getPresets(usb: serial.Serial):
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

  error = b''
  if len(sys.argv) > 1 and sys.argv[1] == '1':
    logging.info(f"Running libcam; Placing image {imgIdx} into folder '{imgFolder}'...")
    subprocess.Popen(
      f"cd {imgFolder} && libcamera-jpeg -n -o {imgIdx}.jpeg",
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
    logging.info('Photo captured successfully...\n')

  else:
    logging.error(f'Camera utility returned the following error(s):\n\n{error.decode()}\n')

  usb.write(f'{USB.P_CAPTURE_IMAGE_DONE.value}\n'.encode())

  return [imgFolder, imgIdx + 1]


def startUpload(imgFolder: str, tcpSocket: socket.socket, usb: serial.Serial):
  """Begins the upload process with the server"""

  logging.info("Starting upload...")
  zipDirLocation = zipdir(f'{imgFolder}')

  logging.info(f"Sending '{zipDirLocation}' to workstation")

  try:
    with open(zipDirLocation, 'rb') as f:
      while True:
        data = f.read(1024)
        if not data:
          break

        tcpSocket.sendall(data)
      
    # TODO delete the .zip and possibly the captures folder
    
  except:
    logging.error(f"Failed to send '{zipDirLocation}' to workstation!\n")

  else:
    logging.info(f"File sent to workstation\n")    

  usb.write(f'{USB.P_FINISH_UPLOAD.value}\n'.encode())

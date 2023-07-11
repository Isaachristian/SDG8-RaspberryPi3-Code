#!/usr/bin/python3

import logging
import socket
import serial

# Project Imports
from utils.startup import *
from utils.USB import USB
from utils.utils import *
from utils.general import *


usb: serial.Serial = init()
imgFolder: str = ''
imgIdx: int = 0
tcpSocket: socket.socket


while True:
  logging.info("Listening for command...")
  
  command = usb.readline().strip().decode()

  if   check(command, Compare.STARTS_WITH,  USB.A_TRY_CONNECT.value): 
    tcpSocket = tryConnection(command, usb)
    
  elif check(command, Compare.EQUALS, USB.A_GET_PRESETS.value): 
    getPresets(usb)

  elif check(command, Compare.STARTS_WITH,  USB.A_SAVE_PRESET.value): 
    writePresetToFile(command, usb)
  
  elif check(command, Compare.EQUALS, USB.A_CAPTURE_IMG.value): 
    imgFolder, imgIdx = captureImage(imgFolder, imgIdx, usb)
  
  elif check(command, Compare.EQUALS, USB.A_STRT_UPLOAD.value): 
    imgFolder = startUpload(imgFolder, tcpSocket, usb)

  elif check(command, Compare.CONTAINS, USB.A_END_PROGRAM.value):
    logging.info("Gracefully exiting per request by ATmega...")
    exit()
  
  else: 
    logging.error(f'Unknown command: {command}\n')


  usb.reset_input_buffer()

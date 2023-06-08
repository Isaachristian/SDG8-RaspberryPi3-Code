#!/usr/bin/python3
from datetime import datetime
import serial
import logging


# CONSTANTS
USB_PORT = "/dev/ttyACM0"  # USB Port Location





# ATTEMPT INITIAL CONNECTION
try:
  usb = serial.Serial(USB_PORT, 9600, timeout = 10)
except:
  date = datetime.now().date()
  logging.basicConfig(filename=f'logs/debug-{date}.log', level=logging.DEBUG)
  logging.debug("ERROR - Could not open USB serial port. Please check your port name and permissions.")
  print("Exiting program.")
  exit()

# Inform the Arduino that the connection has been made


# Send command to Arduino
print("Enter a command...\n")
while True:
  command = input("Enter command: ")
  
  # Read/Print Arduino A0 Pin Value 
  if command == "a":
    usb.write(b'read_a0')
    line = usb.readline()
    line = line.decode()
    line = line.strip()

    print(line)

    if line.isdigit():
      value = int(line)
    else:
      print("Unknown value '" + line + "', setting to 0.")
      value = 0

    print("Arduino A0 value:", value)

  # Turn on the LED
  elif command == "l":
    usb.write(b'led_on')
    print("Arduino LED turned on.")

  # Turn Off the LED
  elif command == "k":
    usb.write(b'led_off')
    print("Arduino LED turned off.")

  # End Program
  elif command == "x":
    print("Exiting program.")
    exit()

  # Unknow command
  else:
    print("Unknown command '" + command + "'.")
    print_commands()
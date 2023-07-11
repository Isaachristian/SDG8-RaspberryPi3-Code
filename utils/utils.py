from enum import Enum
import logging
import os
import zipfile


class Compare(Enum):
  EQUALS = 'Equals'
  STARTS_WITH = 'StartsWith'
  CONTAINS = 'Contains'



def check(command: str, compare: Compare, USBValue: str):
  """Check for a particular command"""
  if compare == Compare.EQUALS:
    return command == USBValue
  
  if compare == Compare.STARTS_WITH:
    return command.startswith(USBValue)

  if compare == Compare.CONTAINS:
    return command in USBValue


def parseIP(ip: str):
  """IPs are being stored as 12 digit strings, this parses them into proper IP"""

  logging.info(f'Attempting to parse {ip}')
  return f'{int(ip[0:3])}.{int(ip[3:6])}.{int(ip[6:9])}.{int(ip[9:12])}'


def zipdir(path):
  """Zips the folder at the given path"""

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
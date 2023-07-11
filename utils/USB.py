from enum import Enum

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
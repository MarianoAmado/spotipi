import time
import sys
import logging
from logging.handlers import RotatingFileHandler
from getSongInfo import getSongInfo
import requests
from io import BytesIO
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import sys,os
import configparser

if len(sys.argv) > 2:
    username = sys.argv[1]
    token_path = sys.argv[2]

    # Configuration file    
    dir = os.path.dirname(__file__)
    filename = os.path.join(dir, '../config/rgb_options.ini')

    # Configures logger for storing song data    
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='spotipy.log',level=logging.INFO)
    logger = logging.getLogger('spotipy_logger')

    # automatically deletes logs more than 2000 bytes
    handler = RotatingFileHandler('spotipy.log', maxBytes=2000,  backupCount=3)
    logger.addHandler(handler)

    # Configuration for the matrix
    config = configparser.ConfigParser()
    config.read(filename)

    options = RGBMatrixOptions()
    options.rows = 64#int(config['DEFAULT']['rows'])
    options.cols = 64#int(config['DEFAULT']['columns'])
    # options.pixel_mapper_config ="Rotate:90"
    # options.rows = int(config['DEFAULT']['rows'])
    # options.cols = int(config['DEFAULT']['columns'])
    # options.chain_length = int(config['DEFAULT']['chain_length'])
    # options.parallel = int(config['DEFAULT']['parallel'])
    options.hardware_mapping = config['DEFAULT']['hardware_mapping']
    options.gpio_slowdown = int(config['DEFAULT']['gpio_slowdown'])
    options.brightness =87 #int(config['DEFAULT']['brightness'])
    options.limit_refresh_rate_hz = int(config['DEFAULT']['refresh_rate'])
    options.drop_privileges = False

    pause_image = os.path.join(dir, config['DEFAULT']['pause_image'])
    pause_img = Image.open(pause_image)
    pause_img.thumbnail((16, 16), Image.Resampling.LANCZOS)
    pause_img.convert('RGBA')
    _, _, _, pause_mask = pause_img.split()


    default_image = os.path.join(dir, config['DEFAULT']['default_image'])
    print(default_image)
    matrix = RGBMatrix(options = options)

    prevSong    = ""
    currentSong = ""
    prevPlaying = False
    matrix_size= int(matrix.width/2)
    bg_img = Image.new("RGBA", (64, 64), (0, 0, 0, 255))

    try:
      while True:
        try:
          song_info = getSongInfo(username, token_path)
          imageURL = song_info[1]
          progress = song_info[2]
          duration = song_info[3]
          playing = song_info[4]
          percentage = 0        


          currentSong = imageURL

          if ( prevSong != currentSong or prevPlaying != playing):
            response = requests.get(imageURL)
            image = Image.open(BytesIO(response.content))
            image.thumbnail((matrix.width, matrix.height), Image.Resampling.LANCZOS)
            
            if ( not playing ):
              image = image.convert("RGBA")
              image = Image.blend(image, bg_img, 0.1)
              image.paste(pause_img, (matrix_size-8, matrix_size-8), pause_mask)

            matrix.Clear()
            matrix.SetImage(image.convert('RGB'))
            
            # matrix.SetImage(pause_img.convert('RGB'))
            prevSong = currentSong
            prevPlaying = playing
          
          if (duration > 0):
            percentage = int(progress * 64 / duration)
            white = graphics.Color(255, 255, 255)
            graphics.DrawLine(matrix, 0, 63, percentage, 63, white)


          time.sleep(1)
        except Exception as e:
          matrix.Clear()
          # image = Image.open(default_image)
          # image.thumbnail((matrix.width, matrix.height), Image.Resampling.LANCZOS)
          # matrix.SetImage(image.convert('RGB'))
          prevSong = ""
          prevPlaying = False

          print(e)
          time.sleep(5)
    except KeyboardInterrupt:
      sys.exit(0)

else:
    print("Usage: %s username" % (sys.argv[0],))
    sys.exit()

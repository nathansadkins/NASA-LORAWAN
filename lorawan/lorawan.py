"""
This code is an adaptation of an example for using the RFM9x Radio with Raspberry Pi and LoRaWAN.
It has been modified to accompany a thermocouple using the MAX31850 amplifier with level shifter.
Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Nathan Adkins
Contact: 6786705086
"""
import threading
import time
import subprocess
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_ssd1306
from adafruit_tinylora.adafruit_tinylora import TTN as Chirpstack
from adafruit_tinylora.adafruit_tinylora import TinyLoRa
import os
import glob
import time

# Thermocouple Setup

# Initialize the thermocouple GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm') # Turns on the Temperature module
 
# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '3b*')[0]
device_file = device_folder + '/w1_slave'
 
# A function that reads the sensors data
def read_temp_raw():
  f = open(device_file, 'r') # Opens the temperature device file
  lines = f.readlines() # Returns the text
  f.close()
  return lines
 
# Convert the value of the sensor into a temperature
def read_temp():
  lines = read_temp_raw() # Read the temperature 'device file'
 
  # While the first line does not contain 'YES', wait for 0.2s
  # and then read the device file again.
  while lines[0].strip()[-3:] != 'YES':
    time.sleep(0.2)
    lines = read_temp_raw()
 
  # Look for the position of the '=' in the second line of the
  # device file.
  equals_pos = lines[1].find('t=')
 
  # If the '=' is found, convert the rest of the line after the
  # '=' into degrees Celsius, then degrees Fahrenheit
  if equals_pos != -1:
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_f

# GPIO Button Setup 

# Button A
btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP
 
# Button B
btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP
 
# Button C
btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP
 
# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
 
# 128x32 OLED Display
reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height
 
# TinyLoRa Configuration
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = DigitalInOut(board.CE1)
irq = DigitalInOut(board.D22)
rst = DigitalInOut(board.D25)
 
# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x01, 0x14, 0xdd, 0x58])
# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray([0x02, 0x61, 0x83, 0x71, 0x96, 0x9a, 0x3b, 0x03,
                   0x0a, 0x5d, 0x50, 0x86, 0xf2, 0xce, 0x19, 0xa5])
# TTN Application Key, 16 Bytess, MSB
app = bytearray([0x5f, 0x78, 0xd5, 0x24, 0xc6, 0x3e, 0x8a, 0x28,
                 0x4c, 0xc8, 0x9e, 0xc3, 0xd3, 0x49, 0x8f, 0x77])
# Initialize ThingsNetwork configuration
cs_config = Chirpstack(devaddr, nwkey, app, country='US')
# Initialize lora object
lora = TinyLoRa(spi, cs, irq, rst, cs_config)
# 2b array to store sensor data
data_pkt = bytearray(2)
# time to delay periodic packet sends (in seconds)
data_pkt_delay = 5.0
 
 
def send_pi_data_periodic():
    threading.Timer(data_pkt_delay, send_pi_data_periodic).start()
    print("Sending periodic data...")
    send_pi_data(temp)
    print('TEMP:', temp)
 
def send_pi_data(data):
    # Encode float as int
    data = int(data * 100)
    # Encode payload as bytes
    data_pkt[0] = (data >> 8) & 0xff
    data_pkt[1] = data & 0xff
    # Send data packet
    lora.send_data(data_pkt, len(data_pkt), lora.frame_counter)
    lora.frame_counter += 1
    display.fill(0)
    display.text('Sent Data to C-Stack!', 1, 10, 5)
    print('Data sent!')
    display.show()
    time.sleep(0.5)
 
while True:
    packet = None
    # draw a box to clear the image
    display.fill(0)
    display.text('RasPi LoRaWAN', 35, 0, 1)
    temp = read_temp()
    temp = float(temp) 
    if not btnA.value:
        # Send Packet
        send_pi_data(temp)
    if not btnB.value:
        # Display CPU Load
        display.fill(0)
        display.text('Temp in F', 45, 0, 1)
        display.text(str(temp), 60, 15, 1)
        display.show()
        time.sleep(0.1)
    if not btnC.value:
        display.fill(0)
        display.text('* Periodic Mode *', 15, 0, 1)
        display.show()
        time.sleep(0.5)
        send_pi_data_periodic()
 
 
    display.show()
    time.sleep(.1)
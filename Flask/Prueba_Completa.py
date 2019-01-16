from flask import Flask, render_template
from flask import request
import RPi.GPIO as GPIO
import time
import sys
import os
import threading
import spidev # To communicate with SPI devices
import requests
from time import sleep
import time
from sys import argv, exit
import math

###################################################################
####################       DATOS SENSORES        ##################

# Start SPI connection
spi = spidev.SpiDev()
spi.open(0,0)

#Database
url = 'https://corlysis.com:8086/write'#Escritura de datos en puerta y website
params = {"db": "raspi05", "u": "token", "p":"ef87b97d9c9cdeb17ee4f0c82f1c0d4d"}

#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
#GPIO.setmode(GPIO.BOARD)
 
#set GPIO Pins
GPIO_TRIGGER = 12 #32 #12
GPIO_ECHO = 26 #37 #26
GPIO_BUZZER = 19 #35 #19
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(GPIO_BUZZER, GPIO.OUT)

####################       DATOS SENSORES        ##################
##################################################################

GPIO.setup(16, GPIO.OUT) #36
GPIO.setup(18, GPIO.OUT) #12
dir = GPIO.PWM(18, 50) #12
mot = GPIO.PWM(16, 50) #36

dir.start(7.5)
mot.start(7.3)

app = Flask(__name__)

#Ejecución de la cámara:
def worker():
    os.system('sudo motion -n')

@app.route('/')
def home():
    #Preparamos hilo para la camara:
    t = threading.Thread(target=worker)
    t.start()
    
    time.sleep(2) # sleep 2 second
    
    #Preparamos hilo para los sensores:
    t2 = threading.Thread(target=main)
    t2.start()
    
    return render_template('Controller.html')

@app.route("/parar")
def estadoNormal():
    mot.ChangeDutyCycle(7.3)
    dir.ChangeDutyCycle(7.5)
    return render_template('Controller.html')

@app.route("/alante")
def alante():
    mot.ChangeDutyCycle(8.5)
    return render_template('Controller.html')

@app.route("/atras")
def atras():
    mot.ChangeDutyCycle(6.5)
    return render_template('Controller.html')

@app.route("/derecha")
def derecha():
    dir.ChangeDutyCycle(2.5)
    return render_template('Controller.html')

@app.route("/izquierda")
def izquierda():
    dir.ChangeDutyCycle(12.5)
    return render_template('Controller.html')

if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

###################################################################
####################       DATOS SENSORES        ##################
        
# this device has two I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# set backlight to (R,G,B) (values from 0..255 for each)
def setRGB(r,g,b):
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

# send command to display (no need for external use)    
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# set display text \n for second line(or auto wrap)     
def setText(text):
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

#Update the display without erasing the display
def setText_norefresh(text):
    textCommand(0x02) # return home
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    while len(text) < 32: #clears the rest of the screen
        text += ' '
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))
 
def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance

# Read MCP3008 data
def analogInput(channel):
    if ((channel > 7) or (channel < 0)):
        return -1
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def temp(channel):
    bValue = 3975 # sensor v1.0 uses thermistor TTC3A103*39H
    a = analogInput(channel) + 1 # call the function to read analog inputs
    resistance = (float)(1023 - a) * 10000 / a
    t = (float)(1 / ((math.log(resistance / 10000) if resistance > 1 else 0 )/ bValue + 1 / 298.15) - 273.15)
    return t

def sound(channel):
    sum = 0;
    for i in range(32):
        sum += analogInput(channel);

    sum >>= 5;
    return sum

def light(channel):
    # Calculate resistance of sensor in K
    # Valor maximo = 626!
    resistance = analogInput(channel)
    return resistance

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def main():
    try:
        while True:
                temperatura = temp(0) #Temperatura
                luminosidad = light(1)#Luminosidad
                sonido = sound(2)#Sonido        
                proximidad = distance()#Proximidad
                
                setText("T: %s " "L: %s " "S: %s " "P: %s" %(truncate(temperatura,2), luminosidad, sonido,proximidad))
                
                #Comprobación de datos para mostrar el LCD con alertas de colores:
                if temperatura > 30:
                    setRGB(255,0,0)
                elif sonido > 750:
                    setRGB(255,0,0)
                    GPIO.output(GPIO_BUZZER, 1)
                    time.sleep(0.2)
                    GPIO.output(GPIO_BUZZER, 0)
                else:
                    setRGB(0,255,0)
                    
                #Comprobación de la proximidad:
                if proximidad < 25:
                    setRGB(255,0,0)
                    GPIO.output(GPIO_BUZZER, 1)
                    time.sleep(0.2)
                    GPIO.output(GPIO_BUZZER, 0)
                    mot.ChangeDutyCycle(6.5)
                    time.sleep(0.25)
                    mot.ChangeDutyCycle(7.3)
                    dir.ChangeDutyCycle(7.5)
                
                #Introducción de datos en la db:
                #payloadTemperatura = "temperature,place=E119 value=%d\n" % (temperatura)
                #payloadLuminosidad = "luminosidad,place=E120 value=%d\n" % (luminosidad)
                #payloadSonido = "sonido,place=E121 value=%d\n" % (sonido)
                
                #requests.post(url, params=params, data=payloadTemperatura)
                #requests.post(url, params=params, data=payloadLuminosidad)
                #requests.post(url, params=params, data=payloadSonido)
                
                sleep(0.25)    
    except IndexError:
        print("please, introduce the ADC chanel in which you want to read from.")
        exit(0)
        
####################       DATOS SENSORES        ##################
##################################################################

if __name__ == '__main__':
    app.run(host = '0.0.0.0',debug=True,port=5000)

# Italiano
# DL485D4-modbus
**Libreria Python per il controllo del DIMMER LED DL485D4**

DL485D4-modbus.py permette in modo semplice e veloce di controllare il dimmer a 4 canale tramite MODBUS, sia delle 4 uscite ma anche dei 6 I/O

## Installazione
- Creare un ambiente virtuale 
- Installare il modulo minimalmodbus tramite il comando pip3 install minimalmodbus
- Scaricare la libreria DL485D4_modbus.py

## Classe DL485D4
La classe deve essere istanziata con l'ID del nodo (default 11), il nome della porta seriale collegata al confertitore RS485 (default /dev/ttyUSB0) e la velocità seriale (default 19200).


# English
# DL485D4-modbus
**Python library for controlling the DL485D4 LED DIMMER**

DL485D4-modbus.py allows you to quickly and easily control the 4-channel dimmer via MODBUS, both the 4 outputs and the 6 I/Os.

## Installation
- Create a virtual environment
- Install the minimalmodbus module using the pip3 install minimalmodbus command
- Download the DL485D4_modbus.py library

## DL485D4 Class
The class must be instantiated with the node ID (default 11), the name of the serial port connected to the RS485 transfer device (default /dev/ttyUSB0), and the serial speed (default 19200).
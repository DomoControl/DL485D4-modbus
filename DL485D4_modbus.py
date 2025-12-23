#!/usr/bin/python3
# Copyright 2024 Luca Subiaco
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html


import sys
import time
import traceback

import minimalmodbus

# Change parameters to connect the DL485D4 Dimmer by MODBUS
SERIAL_PORT = '/dev/ttyUSB0' # set the right serial port
SERIAL_BAUDRATE = 19200 # Set Modbus Baudrate
ID_NODE = 11 # Set DL485D4 ID 
DEBUG = False

"""
Classe per comandare in modo agevole il DIMMER DL485D4 tramite MODBUS
Informazioni tecniche dettagliate su https://wiki.elettro.info/doku.php?id=smart_dimmer_led

Tramite MODBUS si può comandare DL485D4 in tutte le sue funzioni: attivare i 4 canali di uscita passando per le rampe o con accensione/spegnimento immadiato, 
leggere gli ingressi, leggere il valore di tensione di alimentazione, la temperatura del Microcontrollore e la temperatura di sensori esterni DS18B20 collegati ai vari ingressi.
È possibile memorizzare il valore delle intenstà e dei vari parametri disponibili.

La classe presenta dell funzioni utili per il comando / lettura / memorizzazione.
"""


class DL485D4:
    """ Class to control DL485D4 Dimmer by Modbus """
    def __init__(self, id_node=ID_NODE, baudrate=SERIAL_BAUDRATE, port=SERIAL_PORT, debug=DEBUG):
        """ Inizializzazione """
        self.id_node = id_node
        self.baudrate = baudrate
        self.port = port
        self.debug = debug
        self.instrument = minimalmodbus.Instrument(self.port, self.id_node, debug=False)  # port name, slave address (in decimal)
        self.instrument.serial.baudrate = self.baudrate
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.instrument.serial.bytesize = 8
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 0.03  # IMPORTANTE altrimenti perde l'ultimo carattere
        self.instrument.mode = minimalmodbus.MODE_RTU   # rtu or ascii mode
        self.instrument.clear_buffers_before_each_transaction = True

        self.time_delay = 0.08 # Tempo in secondi di ritardo tra comandi consecutivi (se troppo basso non funziona)
        self.backup_data = []

    def backup(self, ch):
        """ Ritorna la configurazione dell'IO """
        start_ind = 1000 + (100 * ch)
        backup_data = []
        for x in range(start_ind, start_ind + 32):
            backup_data.append([x, self.read(x)])
        return backup_data

    def get_temp_micro(self, data):
        """ Ritorna la temperatura converita """
        return int(data) - 270 + 25

    def get_temp_ds18b20(self, data):
        """ Ritorna la temperatura del DS18B20 dal WORD. Massima risoluzione 0.0625 Gradi """
        if data >= 32768:
            return (65535 - data) / 16
        else: 
            return data / 16

    def get_vin(self, data, rvcc=120000, rgnd=470):
        """ 
            Conversione da BYTY 10bit a TENSIONE
            dove all'ingresso del PIN del micro c'è un partitre  
            resistivo dove rvcc è la resistenza che collega il pin all'ingresso
            e rgnd la resistenza dal pin verso massa 0V
        """
        return data * (rvcc + rgnd) / (rgnd * 930.0)

    def io(self, name):
        """ Dato il nome dell'IO ritorna il valore numerico da passare alla libreria modbus """
        if name.lower()=='out1': # Uscita DIMMER 1 di potenza controllo LED
            val = 11
        elif name.lower()=='out2': # Uscita DIMMER 2 di potenza controllo LED
            val = 12
        elif name.lower()=='out3': # Uscita DIMMER 3 di potenza controllo LED
            val = 13
        elif name.lower()=='out4': # Uscita DIMMER 4 di potenza controllo LED
            val = 14
        elif name.lower()=='out1_i': # Uscita DIMMER 1 di potenza controllo LED IMMEDIATA
            val = 21
        elif name.lower()=='out2_i': # Uscita DIMMER 2 di potenza controllo LED IMMEDIATA
            val = 22
        elif name.lower()=='out3_i': # Uscita DIMMER 3 di potenza controllo LED IMMEDIATA
            val = 23
        elif name.lower()=='out4_i': # Uscita DIMMER 4 di potenza controllo LED IMMEDIATA
            val = 24
        elif name.lower()=='out1_e': # Uscita DIMMER 1 con RAMPA e Memorizzazione su EE
            val = 31
        elif name.lower()=='out2_e': # Uscita DIMMER 2 con RAMPA e Memorizzazione su EE
            val = 32
        elif name.lower()=='out3_e': # Uscita DIMMER 3 con RAMPA e Memorizzazione su EE
            val = 33
        elif name.lower()=='out4_e': # Uscita DIMMER 4 con RAMPA e Memorizzazione su EE
            val = 34
        elif name.lower()=='out1_ie': # Uscita DIMMER 1 IMMEDIATA e Memorizzazione su EE
            val = 41
        elif name.lower()=='out2_ie': # Uscita DIMMER 2 IMMEDIATA e Memorizzazione su EE
            val = 42
        elif name.lower()=='out3_ie': # Uscita DIMMER 3 IMMEDIATA e Memorizzazione su EE
            val = 43
        elif name.lower()=='out4_ie': # Uscita DIMMER 4 IMMEDIATA e Memorizzazione su EE
            val = 44
        elif name.lower()=='io1': # I/O 1
            val = 1
        elif name.lower()=='io2': # I/O 2
            val = 2
        elif name.lower()=='io3': # I/O 3
            val = 3
        elif name.lower()=='io4': # I/O 4
            val = 4
        elif name.lower() in ['io5', 'general', 'master']: # I/O 5
            val = 5
        elif name.lower()=='io6': # I/O 6
            val = 6
        elif name.lower() == 'reset':
            val = 97
        elif name.lower() == 'vin': # Lettura Tensione alimentazione
            val = 98
        elif name.lower() == 'temp_micro': # Lettura temperatura rilevata dal MICRO
            val = 99
        elif name.lower() == 'read_out1': # Lettura Valore impostato Uscita 1
            val = 1102
        elif name.lower() == 'read_out2': # Lettura Valore impostato Uscita 2
            val = 1202
        elif name.lower() == 'read_out3': # Lettura Valore impostato Uscita 3
            val = 1302
        elif name.lower() == 'read_out4': # Lettura Valore impostato Uscita 4
            val = 1402
        else:
            print(f"NOT VALID I/O NAME: {name}")
            sys.exit()
            # return False
        if self.debug: print(f"IO {name=} {val=}")
        return val

    def read(self, io):
        """ Funzione per la lettura dei registri """
        try:
            # print(f"READ REGISTER {n:>4} Data:{instrument.read_register(n)}")
            data = self.instrument.read_register(io)
            time.sleep(self.time_delay)
            # print(data)
            return data
        except IOError as e:
            return f"Failed to read register {io} {e}"
        except TypeError as e:
            return f"TypeError to read register {io} {e}"
        except ValueError as e:
            return f"ValueError to read register {io} {e}"

    def reboot(self):
        """ Reboot del Device """
        self.write(97, 1)   

    def reset(self, ch):
        """ Azzera le variabili della EEPROM dello specifico canale """
        start_ind = 1000 + (100 * ch)
        for ind in range(start_ind, start_ind + 32):
            self.write(ind, 0)
            if self.debug: print(ind, self.read(ind))

    def restore(self, data):
        """ Fa il restore dei parametri salvati """
        for a, d in data:
            if self.debug: print(a, d)
            self.write(a, d)

    def setup_io(self, io_type):
        """ 
            Funzione per configurare l'IO
            ATTENZIONE: non viene fatto alcun controllo per verificare
            se quel IO suporta quella specifica funzione.
            io_type: fare riferimento alla pagine wiki https://wiki.elettro.info/doku.php?id=dl485_modbus
        """
        if io_type == "DIGITAL_OUT":
            val = 0b00000001
        elif io_type == "DIGITAL_OUT_INVERTED":
            val = 0b10000001
        elif io_type == "DIGITAL_IN":
            val =  0b00000000
        elif io_type == "DIGITAL_IN_PULLUP":
            val = 0b01000000
        elif io_type == "ANALOG_IN":
            val = 0b00000010
        elif io_type == "DS18B20":
            val = 0b00000100
        if self.debug: val
        return val

    def write(self, io, command, decimal_point=0):
        """ Comando di scrittura IO / Registri """
        try:
            self.instrument._generic_command(
                6, # comando di scrittura
                io, # numero IO (per l'impostazione dell'IO aggiungere 100)
                command, # comando IO
                decimal_point, # number_of_decimals
                1, # num. registri
                0, # numero bits
                False, # signed
            )
            time.sleep(self.time_delay)
            return True
        except Exception as e:
            print(f"DEVICE NOT ANSWER {e} {self.id_node=} {self.port=} {self.baudrate=}")
            return False


if __name__ == "__main__":
    print("=== Test outputs Dimmer DL485 ===")
    d = DL485D4() # istanza della classe

    # Example to command the 4 LED outputs how: 10% 30% 60% 100% 
    
    v = 9

    d.write(d.io('out1_e'), v)
    # # d.write(d.io('out2_e'), v)
    # # d.write(d.io('out3_e'), v)
    d.write(d.io('out4_e'), v)

    print("=========================")

    # d.write(d.io('out1_ie'), v)
    # # time.sleep(0.5)
    # d.write(d.io('out2_ie'), v+1)
    # # time.sleep(0.5)
    # d.write(d.io('out3_ie'), v+2)
    # # time.sleep(0.5)
    # d.write(d.io('out4_ie'), v+3)

    print(d.read(d.io('read_out1')))
    print(d.read(d.io('read_out2')))
    print(d.read(d.io('read_out3')))
    print(d.read(d.io('read_out4')))
    
    print("-------------------")
    d.write(d.io('out1_e'), v+200)
    # d.write(d.io('out2_e'), v+200)
    # d.write(d.io('out3_e'), v+200)
    d.write(d.io('out4_e'), v+200)
    time.sleep(0.5)
    print(d.read(d.io('read_out1')))
    print(d.read(d.io('read_out2')))
    print(d.read(d.io('read_out3')))
    print(d.read(d.io('read_out4')))


    # time.sleep(0.5)
    # d.write(d.io('out1_e'), v+200)
    # time.sleep(0.5)
    # d.write(d.io('out2_e'), v+200)
    # time.sleep(0.5)
    # d.write(d.io('out3_e'), v+200)
    # time.sleep(0.5)
    # d.write(d.io('out4_e'), v+200)

    # print(d.read(1102))
    # time.sleep(0.2)
    # print(d.read(1202))
    # time.sleep(0.2)
    # print(d.read(1302))
    # time.sleep(0.2)
    # print(d.read(1402))

    # print(d.read(1102))
    # time.sleep(0.2)
    # print(d.read(1202))
    # time.sleep(0.2)
    # print(d.read(1302))
    # time.sleep(0.2)
    # print(d.read(1402))
    
    # d.write(d.io('out1_e'), v+200)
    # # d.write(d.io('out2_e'), v+200)
    # d.write(d.io('out3_e'), v+200)
    # d.write(d.io('out4_e'), v+200)
    


    # Example to READ Voltage Power Supply 
    # vadc = d.read(d.io('vin'))
    # v = d.get_vin(vadc) # Convert from ADC to Real Voltage
    # print(f"Voltage Power Supply: {v/10:>2.1f}")
    # END Read Power Supply Voltage

    # Example to READ Micro Temperature 
    # tadc = d.read(d.io('temp_micro')) # In decimi di grado centigrado
    # t = d.get_temp_micro(tadc) # Convert Temp from ADC to Degree
    # print(f"Temperature Micro ATMEGA328PB: {t:>2.1f}")
    # END Read Power Supply Voltage

    # Read I/O 1, 2, 3, 4, 5, 6 status
    # print(d.read(d.io('io1')))
    # print(d.read(d.io('io2')))
    # print(d.read(d.io('io3')))
    # print(d.read(d.io('io4')))
    # print(d.read(d.io('io5')))
    # print(d.read(d.io('io6')))
    # END READ IO Status

    # d.write(101, d.setup_io('DIGITAL_IN'))
    # d.write(102, d.setup_io('DIGITAL_IN'))
    # d.write(103, d.setup_io('DIGITAL_IN'))
    # d.write(104, d.setup_io('DIGITAL_IN'))
    # d.write(105, d.setup_io('DIGITAL_IN'))
    # d.write(106, d.setup_io('DIGITAL_IN'))

    # print(hex(d.read(101)))
    # print(hex(d.read(102)))
    # print(hex(d.read(103)))
    # print(hex(d.read(104)))
    # print(hex(d.read(105)))
    # print(hex(d.read(106)))
    
    # d.write(101, 0x4)
    # print(d.read(101))
    # print(d.read(1))

    # d.write(102, 0x0)
    # print(d.read(102))
    # print(d.read(2))

    # d.write(103, 0x0)
    # print(d.read(103))
    # print(d.read(3))

    # d.write(104, 0x0)
    # print(d.read(104))
    # print(d.read(4))

    # d.write(105, 0x0)
    # print(d.read(105))
    # print(d.read(5))

    # d.write(106, 0x0)
    # print(d.read(106))
    # print(d.read(6))

    # d.write(101, 0x40)
    # print(d.read(101))
    # time.sleep(0.1)
    # print(hex(d.read(101)))
    # time.sleep(0.1)
    # d.write(101, 143)
    # time.sleep(0.1)
    # print(d.read(101))


    # out1 = d.io('out1')
    # print(out1)
    # d.write(out1, 255)
    # time.sleep(1)
    # d.write(out1, 30)
    # time.sleep(1)
    # d.write(out1, 5)
    # time.sleep(1)

    # out2 = d.io('out2')
    # print(out2)
    # d.write(out2, 255)
    # time.sleep(1)
    # d.write(out2, 30)
    # time.sleep(1)


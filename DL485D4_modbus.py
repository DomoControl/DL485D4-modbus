import minimalmodbus
from collections import OrderedDict
import time
import sys


class Dimmer:
    def __init__(self, id_node=11, baudrate=19600, port='/dev/ttyUSB0', ):
        
        self.id_node = id_node
        self.baudrate = baudrate
        self.port = port
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
        
    def io(self, name):
        """ Dato il nome dell'IO ritorna il valore numerico da passare alla libreria modbus """
        if name.lower()=='out1':
            return 11
        elif name.lower()=='out2':
            return 12
        elif name.lower()=='out3':
            return 13
        elif name.lower()=='out4':
            return 14
        if name.lower()=='out1_i':
            return 21
        elif name.lower()=='out2_i':
            return 22
        elif name.lower()=='out3_i':
            return 23
        elif name.lower()=='out4_i':
            return 24
        elif name.lower()=='in1':
            return 1
        elif name.lower()=='in2':
            return 2
        elif name.lower()=='in3':
            return 3
        elif name.lower()=='in4':
            return 4
        elif name.lower() in ['in5', 'general', 'master']:
            return 5
        elif name.lower() == 'reset':
            return 97
        elif name.lower() == 'vin':
            return 98
        elif name.lower() == 'temp_micro':
            return 99
        
    def setup_io(self, io_type):
        """ 
        Funzione per configurare l'IO
        ATTENZIONE: non viene fatto alcun controllo per verificare
        se quel IO suporta quella specifica funzione.
        io_type: fare riferimento alla pagine wiki https://wiki.elettro.info/doku.php?id=dl485_modbus
        """
        if io_type == "DIGITAL_OUT":
            return 0b00000001
        elif io_type == "DIGITAL_OUT_INVERTED":
            return 0b10000001
        elif io_type == "DIGITAL_IN":
            return  0b00000000
        elif io_type == "DIGITAL_IN_PULLUP":
            return 0b01000000
        elif io_type == "ANALOG_IN":
            return 0b00000010
        elif io_type == "DS18B20":
            return 0b00000100
    
    
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
        
    def backup(self, ch):
        start_ind = 1000 + (100 * ch)
        for x in range(start_ind, start_ind + 32):
            self.backup_data.append([x, self.read(x)])
 
    def reset(self, ch):
        """ Azzera le variabili della EEPROM dello specifico canale """
        start_ind = 1000 + (100 * ch)
        for ind in range(start_ind, start_ind + 32):
            self.write(ind, 0)
            print(ind, self.read(ind))

    def restore(self, data):
        for a, d in data:
            print(a, d)
            self.write(a, d)

    def reboot(self):
        self.write(97, 1)
        
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
        except:
            # print("NOT ANSWER")
            return False
        
    def get_vin(self, data, rvcc=120000, rgnd=470):
        """ 
            Conversione da BYTY 10bit a TENSIONE
            dove all'ingresso del PIN del micro c'è un partitre  
            resistivo dove rvcc è la resistenza che collega il pin all'ingresso
            e rgnd la resistenza dal pin verso massa 0V
        """
        return data * (rvcc + rgnd) / (rgnd * 930.0)

    def get_temp_micro(self, data):
        """ Ritoran la temperatura converita """
        return int(data) - 270 + 25
        
    def get_temp_DS18B20(self, data):
        """ Ritorna la temperatura del DS18B20 dal WORD. Massima risoluzione 0.0625 Gradi """
        if data >= 32768:
            return (65535 - data) / 16
        else: 
            return data / 16


if __name__ == "__main__":
    print("Test outputs Dimmer DL485")
    d = Dimmer()
    
    out1 = d.io('out1')
    print(out1)
    d.write(out1, 255)
    time.sleep(1)
    d.write(out1, 30)
    time.sleep(1)

    out2 = d.io('out2')
    print(out2)
    d.write(out2, 255)
    time.sleep(1)
    d.write(out2, 30)
    time.sleep(1)


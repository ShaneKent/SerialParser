from tkinter import *
from tkinter.ttk import *

import os
import sys
import threading
import serial
import platform

try:
    import wmi
except:
    print("For full functionality, please run on Windows.")

class GUI(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.winfo_toplevel().title('AcuVu Inc. - Serial Parser')
        self.minsize(width=400, height=400)
        self.resizable(False, False)
        
        self.com_port = ""
        self.s = None
        self.read = False

        self.connectionarea = ConnectionArea(self)
        self.data_display = DataDisplay(self)
        self.raw_serial_data = RawSerialData(self)

        self.connectionarea.pack(side=TOP, anchor=N, fill=X)
        self.data_display.pack(side=TOP, anchor=N, fill=X)
        self.raw_serial_data.pack(side=TOP, anchor=N, fill=BOTH)
        
        self.protocol('WM_DELETE_WINDOW', self.__destroy__)

    def read_serial(self):
        
        def callback():
            buffer = ""
            r_num = 0
            while self.read is True:
                try:
                    byte = self.s.read(1)     #read one byte of data.
                    if byte == b'\r':
                        r_num += 1
                        self.parse_buffer(buffer, r_num)
                        buffer = ""
                    else:
                        buffer += byte.decode()
                except ClearCommError as e:
                    print('Tried to read from the serial port when it was already closed.')

        t = threading.Thread(target=callback)
        t.start()

    def parse_buffer(self, buffer, r_num):
        self.data_display.record_number.delete(0, END)
        self.data_display.record_number.insert(0, str( int(r_num / 2) ))

        self.raw_serial_data.serial_data.insert(END, str(buffer) + '\n')
        self.raw_serial_data.serial_data.see(END)

        split = buffer.split(',')
        
        if split[0] == '~HSAC':
            x = int('0x' + split[1], 16)
            y = int('0x' + split[2], 16)
            z = int('0x' + split[3], 16)

            self.data_display.accelerometer_data_x.delete(0, END)
            self.data_display.accelerometer_data_x.insert(0, str( x ))

            self.data_display.accelerometer_data_y.delete(0, END)
            self.data_display.accelerometer_data_y.insert(0, str( y ))

            self.data_display.accelerometer_data_z.delete(0, END)
            self.data_display.accelerometer_data_z.insert(0, str( z ))

        if split[0] == '~HSRD':
            d = int("0x" + split[1], 16)

            self.data_display.potentiometer_data.delete(0, END)
            self.data_display.potentiometer_data.insert(0, str( d ))

        if split[0] == '~HSVI':
            ver = str(int("0x" + split[1], 16)) + "." + str(int("0x" + split[2], 16)) + "." + str(int("0x" + split[3], 16)) + "." + str(int("0x" + split[4], 16))

            self.data_display.version_number.delete(0, END)
            self.data_display.version_number.insert(0, ver)

    def __destroy__(self):
        self.destroy()

class ConnectionArea(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.connectionstatus = ConnectionStatus(self)
        self.buttons = Buttons(self)

        self.connectionstatus.pack(side=LEFT, anchor=N, expand=True, fill=X)
        self.buttons.pack(side=LEFT, anchor=N, expand=True, fill=X)

        self.pack(side=TOP, anchor=W)

class ConnectionStatus(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self._init_widgets()
        self._place_widgets()

    def _init_widgets(self):
        self.label_connection = Label(self, text='Connection Status:', anchor=W, font='Consolas 12 bold')
        self.label_hub_board = Label(self, text='USB Hub:', anchor=W, font='Consolas 12 normal')
        self.label_ov_board = Label(self, text='OV116 Board:', anchor=W, font='Consolas 12 normal')
        self.label_mcu_board = Label(self, text='MCU Board:', anchor=W, font='Consolas 12 normal')

        self.hub_status = Label(self, text='Unknown', anchor=W, font='Consolas 12 italic', foreground='grey')
        self.ov_status = Label(self, text='Unknown', anchor=W, font='Consolas 12 italic', foreground='grey')
        self.mcu_status = Label(self, text='Unknown', anchor=W, font='Consolas 12 italic', foreground='grey')

    def _place_widgets(self):
        padding=0

        self.label_connection.grid(row=0, column=0, columnspan=2, padx=padding, pady=padding, sticky='W')
        self.label_hub_board.grid(row=1, column=0, columnspan=1,  padx=padding, pady=padding, sticky='W')
        self.label_ov_board.grid(row=2, column=0, columnspan=1,  padx=padding, pady=padding, sticky='W')
        self.label_mcu_board.grid(row=3, column=0, columnspan=1,  padx=padding, pady=padding, sticky='W')

        self.hub_status.grid(row=1, column=1, columnspan=1,  padx=padding, pady=padding, sticky='W')
        self.ov_status.grid(row=2, column=1, columnspan=1,  padx=padding, pady=padding, sticky='W')
        self.mcu_status.grid(row=3, column=1, columnspan=1,  padx=padding, pady=padding, sticky='W')

        self.pack(side=TOP, anchor=W)



class Buttons(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self._init_widgets()
        self._place_widgets()

    def _init_widgets(self):
        self.scan_button = Button(self, text='Scan for Devices', command=self.scan_for_devices)
        self.connect_button = Button(self, text='Connect to MCU', command=self.connect_to_mcu)
        self.disconnect_button = Button(self, text='Disconnect from MCU', command=self.disconnect_from_mcu)
        self.clear_display = Button(self, text='Clear Display', command=self.clear_raw_area)
        self.send_reboot = Button(self, text='Send Reboot Message', command=self.send_reboot_message)
        self.get_version = Button(self, text='Get Device Version', command=self.send_version_get)

    def _place_widgets(self):
        padding=3

        self.scan_button.grid(row=0, column=0, columnspan=1, padx=padding, pady=padding, sticky='NESW')

        self.connect_button.grid(row=1, column=0, columnspan=1, padx=padding, pady=padding, sticky='NESW')
        self.connect_button.config(state=DISABLED)

        self.disconnect_button.grid(row=2, column=0, columnspan=1, padx=padding, pady=padding, sticky='NESW')
        self.disconnect_button.config(state=DISABLED)

        self.clear_display.grid(row=0, column=1, columnspan=1, padx=padding, pady=padding, sticky='NESW')
        self.clear_display.config(state=NORMAL)

        self.send_reboot.grid(row=1, column=1, columnspan=1, padx=padding, pady=padding, sticky='NESW')
        self.send_reboot.config(state=DISABLED)

        self.get_version.grid(row=2, column=1, columnspan=1, padx=padding, pady=padding, sticky='NESW')
        self.get_version.config(state=DISABLED)

        self.pack(side=TOP, anchor=W)

    def scan_for_devices(self):
        hub_descriptors = 'VID_04B4&PID_6572'
        ov_descriptors = 'VID_05A9&PID_8065'
        mcu_descriptors = 'VID_0403&PID_6015'

        if (platform.system() is 'Windows'):
            c = wmi.WMI()
            wql = "Select * From Win32_USBControllerDevice"
            devices = [device.Dependent for device in c.query(wql)]
        else:
            print('Can not list USB devices on a', platform.system(), 'machine.')
            devices = []

        self.master.connectionstatus.hub_status.config(text='Disconnected', foreground='red')
        self.master.connectionstatus.ov_status.config(text='Disconnected', foreground='red')
        self.master.connectionstatus.mcu_status.config(text='Disconnected', foreground='red')
        self.connect_button.config(state=DISABLED)
        self.disconnect_button.config(state=DISABLED)
        self.send_reboot.config(state=DISABLED)
        self.get_version.config(state=DISABLED)
        self.master.master.read = False

        for device in devices:
            if hub_descriptors in device.DeviceID:
                self.master.connectionstatus.hub_status.config(text='Connected', foreground='green')
            if ov_descriptors in device.DeviceID:
                self.master.connectionstatus.ov_status.config(text='Connected', foreground='green')
            if mcu_descriptors in device.DeviceID:
                self.master.connectionstatus.mcu_status.config(text='Connected', foreground='green')
                self.connect_button.config(state=NORMAL)
            if 'FTDIBUS' in device.DeviceID:
                self.master.master.com_port = device.Name.split("(")[1].split(")")[0]
                
    def connect_to_mcu(self):
        
        self.connect_button.config(state=DISABLED)
        self.disconnect_button.config(state=NORMAL)
        self.send_reboot.config(state=NORMAL)
        self.get_version.config(state=NORMAL)

        try:
            self.master.master.s = serial.Serial(
                port = self.master.master.com_port,
                baudrate = 115200,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                bytesize = serial.EIGHTBITS,
                timeout = 0)
            
        except Exception as e:
            print("Error: Could not open port '" + self.master.master.com_port + "'.")
            print(e)
            return

        if not self.master.master.s.is_open:
            self.master.master.s.open()
        
        self.master.master.read = True
        self.master.master.read_serial()

    def disconnect_from_mcu(self):

        self.connect_button.config(state=NORMAL)
        self.disconnect_button.config(state=DISABLED)
        self.send_reboot.config(state=DISABLED)
        self.get_version.config(state=DISABLED)

        self.master.master.read = False
        self.master.master.s.close()

    def clear_raw_area(self):
        self.master.master.raw_serial_data.serial_data.delete('1.0', END)

    def send_reboot_message(self):
        message = "~SHRB,REBOOT\r"

        self.master.master.raw_serial_data.serial_data.insert(END, message + '\n')
        self.master.master.s.write(message.encode())

    def send_version_get(self):
        message = "~SHGV\r"

        self.master.master.raw_serial_data.serial_data.insert(END, message + '\n')
        self.master.master.s.write(message.encode())

class DataDisplay(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self._init_widgets()
        self._place_widgets()
        self._clear_entries()

    def _init_widgets(self):
        width=10

        self.record_number_label = Label(self, text='Record Number:', anchor=W, font='Consolas 12 bold')
        self.record_number = Entry(self, font='Consolas 12 normal', width=width)

        self.version_number_label = Label(self, text='Version Number:', anchor=W, font='Consolas 12 bold')
        self.version_number = Entry(self, font='Consolas 12 normal', width=width)

        self.potentiometer_data_label = Label(self, text='Rotation Data:', anchor=W, font='Consolas 12 bold')
        self.potentiometer_data = Entry(self, font='Consolas 12 normal', width=width)

        self.accelerometer_data_x_label = Label(self, text='Motion X:', anchor=E, font='Consolas 12 bold')
        self.accelerometer_data_x = Entry(self, font='Consolas 12 normal', width=width)

        self.accelerometer_data_y_label = Label(self, text='Motion Y:', anchor=E, font='Consolas 12 bold')
        self.accelerometer_data_y = Entry(self, font='Consolas 12 normal', width=width)

        self.accelerometer_data_z_label = Label(self, text='Motion Z:', anchor=E, font='Consolas 12 bold')
        self.accelerometer_data_z = Entry(self, font='Consolas 12 normal', width=width)

    def _place_widgets(self):
        padding=1

        self.record_number_label.grid(row=0, column=0, columnspan=1, padx=padding, pady=padding, sticky='W')
        self.record_number.grid(row=0, column=1, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.version_number_label.grid(row=0, column=2, columnspan=1, padx=padding, pady=padding, sticky='W')
        self.version_number.grid(row=0, column=3, columnspan=1, padx=padding, pady=padding, sticky='W')
        
        self.potentiometer_data_label.grid(row=0, column=4, columnspan=1, padx=padding, pady=padding, sticky='W')
        self.potentiometer_data.grid(row=0, column=5, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.accelerometer_data_x_label.grid(row=1, column=0, columnspan=1, padx=padding, pady=padding, sticky='E')
        self.accelerometer_data_x.grid(row=1, column=1, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.accelerometer_data_y_label.grid(row=1, column=2, columnspan=1, padx=padding, pady=padding, sticky='E')
        self.accelerometer_data_y.grid(row=1, column=3, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.accelerometer_data_z_label.grid(row=1, column=4, columnspan=1, padx=padding, pady=padding, sticky='E')
        self.accelerometer_data_z.grid(row=1, column=5, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.pack(side=TOP, fill=X)

    def _clear_entries(self):
        self.record_number.delete(0, END)
        self.record_number.insert(0, "0")

        self.version_number.delete(0, END)
        self.version_number.insert(0, "Unknown")

        self.potentiometer_data.delete(0, END)
        self.potentiometer_data.insert(0, "0")

        self.accelerometer_data_x.delete(0, END)
        self.accelerometer_data_x.insert(0, "0")

        self.accelerometer_data_y.delete(0, END)
        self.accelerometer_data_y.insert(0, "0")

        self.accelerometer_data_z.delete(0, END)
        self.accelerometer_data_z.insert(0, "0")

class RawSerialData(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self._init_widgets()
        self._place_widgets()
        self._clear_entries()

    def _init_widgets(self):
        width=10

        self.serial_data = Text(self, font='Consolas 12 normal', width=width, state=NORMAL)

    def _place_widgets(self):
        padding=5

        self.serial_data.pack(side=TOP, fill=BOTH, expand=1, padx=padding, pady=padding)#.grid(row=0, column=1, columnspan=1, padx=padding, pady=padding, sticky='W')

        self.pack(side=TOP, fill=BOTH, expand=1)

    def _clear_entries(self):
        self.serial_data.delete('1.0', END)

def main():
    app = GUI()
    app.mainloop()

if __name__ == "__main__":
    if (sys.version_info < (3, 0)):
        print("Use Python 3.6 or greater.")
        sys.exit(-1)

    main()
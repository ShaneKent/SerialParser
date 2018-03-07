import os
import io
import sys
import csv
import math
import glob
import time
import shutil
import serial.tools.list_ports_osx
import matplotlib.pyplot as plt

# pip install tox
# pip install pyserial

def check_arguments():

    if len(sys.argv) != 4:
        print(len(sys.argv))
        print("Usage: python parser.py <output-folder-name> <port-number> <recording-time-seconds>")
        sys.exit(-1)

    return (sys.argv[-3], sys.argv[-2], sys.argv[-1])

def check_filename(filename):

    if os.path.isfile(filename) or os.path.isdir(filename):    
        ans = ""
        while ans is not "Y" and ans is not "n":
            ans = raw_input("Path/filename " + filename + " already exists. Overwrite? [Y/n] ")
        
        if ans == 'n':
            print('Cancelling. Please provide a filename that doesn\'t already exist.')
            exit(-1)
        
    if os.path.isfile(filename):
        os.remove(filename)     # Deletes the file with that name.
    elif os.path.isdir(filename):
        shutil.rmtree(filename) # Deletes the directory with that name.

    os.mkdir(filename)

    return filename + '/'

def check_port_number(port_number):

    if sys.platform.startswith('win'):
        ports = ['COM' + str(i) for i in range(1, 257)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    
    else:
        raise EnvironmentError('Unsupported platform')

    for port in ports:
        if port_number in port:
            return port

    print('Provided port number doesn\'t exist. Available ports include:')
    for port in ports:
        print('\t' + port)
    exit(-1)
    
    return

def collect_data(port, recording_time):

    s = open_port(port)

    recording_time = int(recording_time)
    start_time = time.time()
    data = []
    buffer = ""

    print("Beginning data collection...")
    while time.time() - start_time < recording_time:
        byte = s.read(1)     #read one byte of data.
        
        if byte == b'\r':
            data.append(buffer)
            buffer = ""
        else:
            buffer += byte.decode()

    print("Data collection completed - collected " + str(len(data)) + " points of data.")

    s.close()

    return data

def open_port(port_name):

    try:
        s = serial.Serial(
            port = port_name,
            baudrate = 115200,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = 0)
    except:
        print("Error: Could not open port '" + port_name + "'.")
        exit(-1)

    if not s.is_open:
        s.open()

    return s

def open_file(filename):

    lines = list()
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
            if len(lines) == 1:
                lines = lines[0].split('\r')

    except IOError:
        print("Provide a text file with a raw serial data stream.")
        print("Usage: python parser.py <filename> [optional-port-number]")
        exit(-1)

    return lines

def parse_data(filename, lines):

    p_raw = []
    a_raw = []
    pot_data = [['Sample Number', 'Potentiometer Data']]
    accel_data = [['Sample Number', 'X Data', 'Y Data', 'Z Data']]
    
    i = 0
    j = 0

    for line in lines:
        split = line.split(',')
        
        if split[0] == '~HSAC':
            x = int('0x' + split[1], 16)
            y = int('0x' + split[2], 16)
            z = int('0x' + split[3], 16)

            a_raw.append((i, x, y, z))
            
            accel_data.append(
                {"Sample Number" : i, "X Data" : x, "Y Data" : y, "Z Data" : z}
            )
            i += 1
        
        if split[0] == '~HSRD':
            d = int("0x" + split[1], 16)
            
            p_raw.append((j, d))
            
            pot_data.append(
                {"Sample Number" : j, "Potentiometer Data" : d}
            )
            j += 1

    if len(accel_data) > len(pot_data):
        a_raw = a_raw[:-1]
        accel_data = accel_data[:-1]
    elif len(pot_data) > len(accel_data):
        p_raw = p_raw[:-1]
        pot_data = pot_data[:-1]

    write_to_output(filename + "accel", accel_data)
    write_to_output(filename + "pot", pot_data)

    return (a_raw, p_raw)

def write_to_output(name, data):

    with open(name + '.csv', 'w') as csvfile:
        field_names = data.pop(0)
        writer = csv.DictWriter(csvfile, fieldnames=field_names)

        writer.writeheader()
        for data in data:
            writer.writerow(data)

    return

def plot_potentiometer(filename, sample_num, data):
    """
    Normalize the data to comparse to the accelerometer data.
    """

    min_data = min(data)
    max_data = max(data)

    try:
        normalized = [float(x - min_data)/float(max_data - min_data) for x in data]
    except ZeroDivisionError:
        normalized = [float(x - min_data)/0.00001 for x in data]

    plt.plot(sample_num, normalized)
    plt.ylabel('Normalized Potentiometer Value')
    plt.xlabel('Sample Number')
    plt.title('Potentiometer Value with Respect to Time')

    plt.tight_layout()
    plt.savefig(filename + 'pot.png')

    plt.clf()

    return normalized

def plot_accelerometer(filename, sample_num, data):
    """
    Normalize the vector data and plot the x, y, and z components.
    """

    magnitude = [math.sqrt((i[0] ** 2) + (i[1] ** 2) + (i[2] ** 2)) for i in data]

    min_data = min(magnitude)
    max_data = max(magnitude)

    try:
        normalized = [float(x - min_data)/float(max_data - min_data) for x in magnitude]
    except ZeroDivisionError:
        normalized = [float(x - min_data)/0.00001 for x in magnitude]

    plt.plot(sample_num, normalized)
    plt.ylabel('Normalized Accelerometer Data')
    plt.xlabel('Sample Number')
    plt.title('Accelerometer Data with Respect to Sample Number')

    plt.tight_layout()
    plt.savefig(filename + 'accel.png')

    plt.clf()

    return normalized

def plot_both(filename, sample_num, pot_norm, accel_norm):

    plt.plot(sample_num, pot_norm, sample_num, accel_norm)
    plt.ylabel('Normalized Sensor Data')
    plt.xlabel('Sample Number')
    plt.title('Combined Sensor Data with Respect to Sample Number')
    plt.legend(['Potentiometer', 'Accelerometer'], fontsize='x-small')

    plt.tight_layout()
    plt.savefig(filename + 'both.png')

    plt.clf()

    return


if __name__ == "__main__":

    filename, port_number, recording_time = check_arguments()
    
    path = check_filename(filename)
    port = check_port_number(port_number)
    data = collect_data(port, recording_time)

    try:
        (accel, pot) = parse_data(path, data)

        sample_num = [sample[0] for sample in accel]
        accel      = [(sample[1], sample[2], sample[3]) for sample in accel]
        pot        = [sample[1] for sample in pot]

        pot_norm   = plot_potentiometer(path, sample_num, pot)
        accel_norm = plot_accelerometer(path, sample_num, accel)

        plot_both(path, sample_num, pot_norm, accel_norm)
    except Error as e:
        print("Something went wrong!")
        print(e)
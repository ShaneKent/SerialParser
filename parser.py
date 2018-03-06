import os
import sys
import csv
import math
import matplotlib.pyplot as plt

def check_arguments():

    if len(sys.argv) != 2:
        print("Usage: python parser.py <filename>")
        sys.exit(-1)

    return sys.argv[-1]

def open_file(filename):
    lines = list()
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
    except IOError:
        print("Provide a text file with a raw serial data stream.")
        print("Usage: parser.py <filename>")
        exit(-1)

    return lines

def parse_data(filename, lines):

    p_raw = []
    a_raw = []
    pot_data = [['Sample Number', 'Potentiometer Data']]
    accel_data = [['Sample Number', 'X Data', 'Y Data', 'Z Data']]
    
    i = j = 0
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

def plot_potentiometer(filename, sample_num, data):
    """
    Nothing special needs to be done to the potentiometer data before plotting it.
    """
    plt.plot(sample_num, data)
    plt.ylabel('Potentiometer Value')
    plt.xlabel('Sample Number')
    plt.title('Potentiometer Value with Respect to Time')

    plt.savefig(filename + 'plot.png')

def plot_accelerometer(filename, sample_num, data):
    """
    Normalize the vector data and plot the x, y, and z components.
    """

    x = []
    y = []
    z = []

    for vector in data:
        magnitude = math.sqrt( (vector[0] ** 2) + (vector[1] ** 2) + (vector[2] ** 2))
        
        x.append( vector[0] / magnitude )
        y.append( vector[1] / magnitude )
        z.append( vector[2] / magnitude )

    plt.subplot(3, 1, 1)
    plt.plot(sample_num, x)
    plt.ylabel('X-Axis')
    plt.xlabel('Sample Number')
    plt.title('Normalized X Axis with Respect to Time')
    
    plt.subplot(3, 1, 2)
    plt.plot(sample_num, y)
    plt.ylabel('Y-Axis')
    plt.xlabel('Sample Number')
    plt.title('Normalized Y Axis with Respect to Time')
    
    plt.subplot(3, 1, 3)
    plt.plot(sample_num, z)
    plt.ylabel('Z-Axis')
    plt.xlabel('Sample Number')
    plt.title('Normalized Z Axis with Respect to Time')
    
    plt.tight_layout()
    plt.savefig(filename + 'accel.png')

if __name__ == "__main__":
    filename = check_arguments()
    lines = open_file(filename)
    path = filename.split('.')[0] + '/' # Get the text before the file extension.

    try:
        os.stat(path)
    except:
        os.mkdir(path)

    (accel, pot) = parse_data(path, lines)

    sample_num = [sample[0] for sample in accel]
    accel      = [(sample[1], sample[2], sample[3]) for sample in accel]
    pot        = [sample[1] for sample in pot]
    
    plot_potentiometer(path, sample_num, pot)
    plot_accelerometer(path, sample_num, accel)

    
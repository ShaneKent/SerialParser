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
            if len(lines) == 1:
                lines = lines[0].split('\r')

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
    plt.savefig(filename + 'plot.png')

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
    plt.ylabel('Sensor Data')
    plt.xlabel('Sample Number')
    plt.title('Potentiometer and Accelerometer Data with Respect to Sample Number')
    plt.legend(['Potentiometer', 'Accelerometer'], fontsize='xx-small')

    plt.tight_layout()
    plt.savefig(filename + 'both.png')

    plt.clf()


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

    pot_norm   = plot_potentiometer(path, sample_num, pot)
    accel_norm = plot_accelerometer(path, sample_num, accel)

    plot_both(path, sample_num, pot_norm, accel_norm)
    
import serial,time #You need the pyserial library
import struct      #For packing data into bytes
import sys
import getopt

command = None
filename = None
romsize = 1

def display_romsize(romsize:int):
    if romsize >= 1024*1024:
        print("Eprom size:",romsize/(1024*1024),"MB\n")
    else:
        print("Eprom size:",romsize/(1024),"KB\n")

def get_filename():
    if filename is not None:
        return filename
    return input("What's the name of the file? ")

try:
    opts, args = getopt.getopt(sys.argv[1:],"hc:f:s:",["command=","file=","romsize"])
except getopt.GetoptError:
    print('eprom.py -c <command_number> -f <filename> -s <romsize>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print('')
        print('Usage:')
        print('eprom.py -c <command_number> -f <filename> -s <romsize>')
        print('')
        print('         command_number - numeric value from main menu')
        print('         file_name      - relative filename to use in read / burn commands')
        print('         romsize        - used EPROM size as a fraction of a megabyte')
        print('')
        sys.exit()
    elif opt in ("-c", "--command"):
        command = int(arg)
    elif opt in ("-f", "--file"):
        filename = arg
    elif opt in ("-s", "--romsize"):
        romsize = float(arg)
    else:
        print(opt, arg)

if command is None:
    print("        ________    _________    _________    _________    _____________ ")
    print("      /  ______/|  /  ___   /|  /  ___   /|  /   __   /|  /  _    _    /|")
    print("     /  /_____ |/ /  /__/  / / /  /__/  / / /  /  /  / / /  / /  / /  / /")
    print("    /  ______/|  /   _____/ / /     ___/ / /  /  /  / / /  / /  / /  / / ")
    print("   /  /______|/ /  / _____|/ /  /\  \__|/ /  /__/  / / /  / /  / /  / /  ")
    print("  /________/|  /__/ /       /__/ /\__/|  /________/ / /__/ /__/ /__/ /   ")
    print("  |________|/  |__|/        |__|/ |__|/  |________|/  |__|/|__|/|__|/    ")
    print("\n")
    print("  Robson Couto       2016 www.dragaosemchama.com.br https://github.com/robsoncouto/eprom ")
    print("  Marcin Jóżwikowski 2020 www.jozwikowski.pl        https://github.com/marcin-jozwikowski/eprom\n")

#Default value, 1MB chip:
romsize=romsize*1024*1024
numsectors=int(romsize/128) # I am sending data in 128 byte chunks
try:
    ser = serial.Serial('/dev/ttyACM0', 250000, timeout=0)
except Exception as e:
    print("Exception occured during serial initialize:", e)

time.sleep(1);#my arduino bugs if data is written to the port after opening it

while True:
    if command is None:
        display_romsize(romsize)
        print("  What would you like to do?      ")
        print("                                  ")
        print("          1-Read eprom            ")
        print("          2-Burn eprom            ")
        print("          3-About this script     ")
        print("          4-Blank check           ")
        print("          5-Select chip size      ")
        print("          6-Verify eprom          ")
        print("                                  ")
        print("          7-Quit                \n")
        #get option from user:
        option=int(input("Please insert a number: "))
    else:
        option = command

    #Read EPROM
    if(option==1):
        name=get_filename()
        f = open(name, 'w')
        f.close()
        ser.flushInput()
        ser.write(b"\x55")
        ser.write(bytes("r","ASCII"))
        numBytes=0
        f = open(name, 'ab')
        #I just read the data and put it into a file.
        #TODO - Checksum scheme as when burning
        while (numBytes<romsize):
            while ser.inWaiting()==0:
                print("Reading from eprom. Current porcentage: {:.2%}".format(numBytes/romsize),end='\r')
                time.sleep(0.1)
            data = ser.read(1)#must read the bytes and put in a file
            f.write(data)
            numBytes=numBytes+1
        f.close()
        print("\nDone\n")
    #Burn EPROM, see schematic at my website
    if(option==2):
        name=get_filename()
        f = open(name, 'rb')
        for i in range(numsectors):
            ser.write(b"\x55")
            ser.write(bytes("w","ASCII" ))
            time.sleep(0.001)
            #send address of the block first
            ser.write(struct.pack(">B",i>>8))
            CHK=i>>8
            time.sleep(0.001)
            ser.write(struct.pack(">B",i&0xFF))
            CHK^=i&0xFF
            time.sleep(0.001)
            data=f.read(128)
            #print(data)

            #Gets checksum from xoring the package
            for j in range(len(data)):
                 CHK=CHK^data[j]
            time.sleep(0.001)
            print("Writing data. Current porcentage: {:.2%}".format(i/numsectors),end='\r')
            #print("CHK:", CHK)
            response=~CHK

            #keeps trying while the replied checksum is not correct
            while response!=CHK:
                ser.write(data)
                ser.write(struct.pack(">B",CHK&0xFF))
                timeout=30
                while ser.inWaiting()==0:
                    time.sleep(0.01)
                    timeout=timeout-1
                    if timeout==0:
                        print("could not get a response, please start again\n")
                        break
                response=ord(ser.read(1))
                if response!=CHK:
                    print("wrong checksum, sending chunk again\n")
        f.close()

    #Just some info
    if(option==3):

        print("\nA more detailed write up about this project is available at www.dragaosemchama.com.br")
        print("This script goes together with a Arduino sketch, both are used to read and program")
        print("eproms on the cheap.")
        print("Written by Robson Couto\n")
    #Blank check
    if(option==4):
        #same as reading
        ser.flushInput()
        ser.write(b"\x55")
        ser.write(bytes("r","ASCII"))
        numBytes=0
        blank=1
        while (numBytes<romsize):
            while ser.inWaiting()==0:
                print("Reading from eprom. Current porcentage: {:.2%}".format(numBytes/romsize),end='\r')
                time.sleep(0.1)
            data = ser.read(1)
            numBytes=numBytes+1
            if ord(data)!=255:
                blank=0
                break
        #Ends check on first byte not erased
        if blank==1:
            print("\nThe chip is blank\n")
        else:
            print("\nThe chip seems to contain data\n")
        print("Done\n")
    #Change size of EPROM, for reading EPROMs other than 1MB
    if(option==5):
        display_romsize(romsize)
        megs=float(input("Please insert the size of the eprom in Megabytes: "))
        romsize=megs*1024*1024
        numsectors=int(romsize/128) # I am sending data in 128 byte chunks
    #This is for checking if the eprom was programmed right
    if(option==6):
        #Reads each byte and compares with a byte in the file
        print("This compares a eprom with a file in the script folder\n")
        name=input("\nWhat's the name of the file?\n")
        f = open(name, 'rb')
        ser.flushInput()
        ser.write(b"\x55")
        ser.write(bytes("r","ASCII"))
        numBytes=0
        while (numBytes<romsize):
            while ser.inWaiting()==0:
                print("Reading from eprom. Current porcentage: {:.2%}".format(numBytes/romsize),end='\r')
                time.sleep(0.01)
            eprom_byte = ser.read(1)
            file_byte = f.read(1)
            if(eprom_byte!=file_byte):
                #the \033[031m and \033[0m sequence are ansi sequences that turn text red and cancel it respectively
                #I dont know how windows handle them
                print("\n\033[31mFound mismatch at ",hex(f.tell()))
                print("- eprom byte: ",hex(ord(eprom_byte))," - file byte: ",hex(ord(file_byte)),"\033[0m\n")
            numBytes=numBytes+1
        print("\nDone\n")
    if(option==7):
        print("See ya!")
        break

    if command is not None:
        sys.exit()

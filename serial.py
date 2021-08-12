import os.path
import ctypes

# this is the name of a file that will be on our hardware, but is unlikely to be on another drive
SENTINEL_NAME = "SportsDatabase.txt"
SERIAL_MODULE = 'serial_local'

# create shorter pointers to win32 functions
CreateFile = ctypes.windll.kernel32.CreateFileA
GetVolumeInformation = ctypes.windll.kernel32.GetVolumeInformationA
GetLogicalDrives = ctypes.windll.kernel32.GetLogicalDrives

def get_mounted_volumes():
    ret = []
    drive_mask = GetLogicalDrives()
    for i in range(26):
        this_mask = 2**i
        if this_mask&drive_mask:
            # found drive. convert bitmask value to 
            ret.append("%s:" % chr(ord("A")+i))
    return ret	    
    

def get_hardware_serial(volume_name=None):
    """Get the hardware serial number for the given volume.

    If volume == None, get the serial number for the volume
    that this file lives on
    """
    serial_len = 32
    serial = ctypes.create_string_buffer("\000" * serial_len)
    volume_len = 32
    volume = ctypes.create_string_buffer("\000" * volume_len)

    if volume_name is None:
        for vol in get_mounted_volumes():
            f = CreateFile(os.path.join(vol, '/', SENTINEL_NAME),
                           0,0,0,3,0,0)
            if f > 0:
                print f
                volume_name = vol
        
    volume_root = "%s\\" % volume_name
    GetVolumeInformation(volume_root, volume, volume_len , serial, None,
                            None, None, 0)
    val = serial.value[::-1]
    return ''.join([hex(ord(c)).replace('0x','') for c in val])

def confirm_hardware_serial():
    import serial_local
    actual_serial = get_hardware_serial()
    expected_serial = serial_local.SERIAL
    return actual_serial == expected_serial


if __name__ == '__main__':
	serial = get_hardware_serial()
 	print "serial #: %s" % serial

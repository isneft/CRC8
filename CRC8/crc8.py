
import binascii

class CRC8():
    def __init__(self):
        poly = 0x07
        mask = 0xFF
        self.TABLE = [0 for i in range(256)]

        for i in range(256):
	    c = i
	    for j in range(8):
	        if (c & 0x80):
                    c = (((c << 1)&mask) ^ poly);
	        else:
                    c <<= 1;
	        j+=1
            
	    self.TABLE[i] = hex(c);
            i+=1
        

    def make_crc8(self, data_str):
        crc8="0x00"
        for i in range(len(data_str)):
            crc8 = self.TABLE[int(crc8,16)^int(binascii.hexlify(data_str[i]),16)]

        return crc8

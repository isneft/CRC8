#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import time
import binascii

byte=1024
brt = 9600

def setSerial(mybaudrate,timeout=None):
    com = serial.Serial(
        port     = '/dev/ttyUSB0',
        baudrate = mybaudrate,
        bytesize = serial.EIGHTBITS,
        parity   = serial.PARITY_NONE,
        timeout  = timeout,
        xonxoff  = False,
        rtscts   = False,
        writeTimeout = None,
        dsrdtr       = False,
        interCharTimeout = None)
 
    com.flushInput()
    com.flushOutput()
    return com


def receive():
    com=setSerial(brt)
    com.flushInput()
    text = ""
    text = com.readline()
    com.close()
    return text

def send(text):
    com=setSerial(brt)
    com.write(text)
    com.flushInput()
    print text
    com.close()

def receive_part():
    text_all=""
    reading_flag=0
    finish_flag=0
    while True:
        print "ready"
    
        outtext = receive()
    
        if "start" in outtext:
            text_all=""
            reading_flag=1

        if reading_flag==1:
            #check sum
            #try:
            if True:
                print outtext
                
                check_sum_right=outtext.split(",")[1]
                outtext_target = outtext.split(",")[2]

                out=""
                for i in range(2,len(outtext.split(","))):
                    if i != 2:
                        out = out + "," + outtext.split(",")[i]
                    else:
                        out += outtext.split(",")[i]

                outtext_target = out
                if "start" in outtext_target:
                    check_target = outtext_target.split("data_beginning")[1]
                elif "end" in outtext_target:
                    check_target = outtext_target.split("&end")[0]
                else:
                    check_target = outtext_target
                    
                check_target = check_target.replace("\r\n","")
                check_sum=0

                if len(check_target)%2==1:
                    check_target = check_target+"0"

                for check in range(len(check_target)/2):
                    target=check_target[check*2:(check+1)*2]
                    num16 = binascii.b2a_hex(target)
                    check_sum+=int(num16,16)

            #except:
                #check_sum = 0

            
            if check_sum == int(check_sum_right):
                print "check OK"
                
                if outtext_target not in text_all:
                    text_all = text_all + outtext_target
                packetNum = (outtext[:3])
                ACK = "ACK,%s"%packetNum
                send(ACK)
                print "ACK"

        if "end" in outtext:
            reading_flag=0
            finish_flag=1
            print "finish\r\n"
            break

    return text_all

def send_part(send_data):
    start = time.time()
    for i in range(int(float(len(send_data)/byte))+1):
        
        packetNum = "%d"%i
        if len(packetNum)==1:
            packetNum = "00"+ packetNum
        elif len(packetNum)==2:
            packetNum = "0" + packetNum

        check_sum_org = send_data[i*byte:(i+1)*byte]

        if "start" in check_sum_org:
            check_sum_org = check_sum_org.split("data_beginning")[1]
        if "end" in check_sum_org:
            check_sum_org = check_sum_org.split("&end")[0]
            
        check_sum=0

        if len(check_sum_org)%2==1:
            check_sum_org = check_sum_org+"0"
            
        for check in range(len(check_sum_org)/2):
            target=check_sum_org[check*2:(check+1)*2]
            num16 = binascii.b2a_hex(target)
            check_sum+=int(num16,16)

        check_sum_str = str(check_sum)
        send_message = packetNum + "," + check_sum_str + "," +send_data[i*byte:(i+1)*byte] + "\r\n"
        print send_message


        for j in range(50):
            com = setSerial(brt)
            send_start=time.time()
            com.write(send_message)
            com.flushInput()
            com.close()
            send_finish = time.time() - send_start
            com = setSerial(brt,0.5)
            ACK=com.readline()
            
            ACK_time=time.time()-send_start
            #print send_finish
            #print ACK_time
            
            if packetNum in ACK:
                print str(i)+"/"+str(int(float(len(send_data)/byte))+1)
                print "OK" + packetNum
                mins = int(ACK_time*(int(float(len(send_data)/byte))+1-i)/60)
                secs = int(ACK_time*(int(float(len(send_data)/byte))+1-i))-mins*60
                print "remining time : %d min %d sec"%(mins,secs)
                print ""
                print ""
                print ""
                
                com.close()
                break
            else:
                print "error"
                com.close()
    end = time.time()
    print "send finifh : %d min"%(int(float(end-start)/60)+1)


def main():
    receive_text=receive_part()
    text_all = receive_text.replace("\r\n","")
    text_all = text_all.replace("\n","")
    send_part(text_all)
    
if __name__=="__main__":
    main()

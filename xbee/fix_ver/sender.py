#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import time
import cv2
import numpy as np
import binascii


byte=1024
brt=9600
comvert=1

def capture_camera(mirror=True, size=None):
    """Capture video from camera"""
    cap = cv2.VideoCapture(0) 
    for i in range(10):
        ret, frame = cap.read()

        if mirror is True:
            frame = frame[:,::-1]

        cv2.imshow('camera capture', frame)

        k = cv2.waitKey(1)
        if k == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return frame


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
 
    #bufferクリア
    com.flushInput()
    com.flushOutput()
    return com

def receive():
    com=setSerial(brt)
    com.flushInput()
    text = ""
    text = com.readline()
    #print text
    com.close()
    return text

def send(text):
    com=setSerial(brt)
    com.write(text)
    #print text
    com.flushInput()
    com.close()


def make_data_stream():
    image = capture_camera()
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    orgHeight, orgWidth = image.shape[:2]
    size = (orgHeight/comvert, orgWidth/comvert)
    halfImg = cv2.resize(image, size)

    image=halfImg
    cv2.imwrite("../log/gray_scale_origin.png", image)
    image_strate = np.reshape(image,(1,np.shape(image)[0]*np.shape(image)[1]))

    out_size=[size[0],size[1]]
    
    return image_strate, out_size

def data_to_text(picture_data, image_size):
    data16=""
    for i in range(np.shape(picture_data)[1]):
        data16 += hex((picture_data[0][i]))[2:]
    short_text=""
    for i in range(len(data16)/2):
        short_text += binascii.a2b_hex(data16[i*2:i*2+2])

    text = "start:%d:%d:data_beginning"%(image_size[0],image_size[1])
    text = text + short_text + "&end\r\n"

    print "image size : %d KB"%int(len(text)*8/1024)
    print "data length : %d" %len(short_text)
    
    return text

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
        #print send_message


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
            try:
            #if True:
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

                if check_sum == int(check_sum_right):
                    print "check OK"
                
                    if outtext_target not in text_all:
                        text_all = text_all + outtext_target
                    packetNum = (outtext[:3])
                    ACK = "ACK,%s"%packetNum
                    send(ACK)
                    print "ACK"

            except:
                check_sum = 0
                check_sum_right = 200

            


        if "end" in outtext:
            reading_flag=0
            finish_flag=1
            print "finish\r\n"
            break

    return text_all


def decode_part(text_all):
    text_all = text_all.replace("\r\n","")
    text_all = text_all.replace("\n","")
    image_pixel = text_all.split("data_beginning")[1]
    image_pixel = image_pixel.split("&end")[0]


    size_y=int(text_all.split(":")[1])
    size_x=int(text_all.split(":")[2])

    image_strate = np.zeros((1,size_x*size_y))
 
    ignore=0
    yes=0
    corect=0

    for i in range(size_x*size_y):
        try:
            
            #image_strate[0,i]=int(image_pixel[i*2:(i+1)*2],16)
            target = binascii.b2a_hex(image_pixel[i])
            image_strate[0,i] = int(target,16)
            yes+=1
        except:
            ignore+=1



    print yes
    print corect
    print ignore

    image = np.zeros((size_x,size_y), np.uint8)
    for i in range(size_x):
        for j in range(size_y):
            image[i,j]=int(image_strate[0,i*size_y+j])
            
    ##reshape(image_strate,(size_x,size_y))
    
    cv2.imwrite("log/gray_scale.png", image)

    cv2.imshow("image",image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print "finish"



def main():
    picture_data, out_size = make_data_stream()
    text_data = data_to_text(picture_data, out_size)
    send_part(text_data)
    receive_text=receive_part()
    decode_part(receive_text)
    #decode_part(text_data)
    
if __name__=="__main__":
    main()

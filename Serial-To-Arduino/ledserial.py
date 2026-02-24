import serial, time
ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
time.sleep(2.5)
ser.reset_input_buffer()

ser.write(b"CL\n"); ser.flush()
print("RX1:", ser.readline().decode(errors="ignore").strip())

ser.write(b"552550000001\n"); ser.flush()   # l=5 c=5 vermelho intensidade 1
print("RX2:", ser.readline().decode(errors="ignore").strip())

ser.close()
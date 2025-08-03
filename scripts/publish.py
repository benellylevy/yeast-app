import json
import paho.mqtt.client as paho

def Publish_stats(temp,DeadBand,Channel_temp_control_enum,Start_T_Control):
    val = {"Temp_setpoint_C":temp,"Deadband_C":DeadBand,"Channel_temp_control_enum":Channel_temp_control_enum,"Start_T_Control?":Start_T_Control}
    json_object = json.dumps(val)
    print(json_object)
    broker="localhost"
    port=1883
    def on_publish(client,userdata,result):             #create function for callback
        print("data published \n")
        pass
    client1= paho.Client("control1")                           #create client object
    client1.on_publish = on_publish                          #assign function to callback
    client1.connect(broker,port)                                 #establish connection
    client1.publish("command/T_controller", json_object)


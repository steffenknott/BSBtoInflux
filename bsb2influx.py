#!/usr/bin/python3
import requests, json, time
from influxdb import InfluxDBClient
from os.path import expanduser, exists

ADAPTERADDRESS = "192.168.0.1"
FIELDS="8310,8316,8330,8332,8700,8703,8704,8741,8744,8950,7870,7881,7884,7730,7760"
INTERVAL = 15 # in seconds, set to -1 to disable looping (e.g. when interval is controlled by cronjob
COMMONTAG = "device" # InfluxDB Tag that should be written with every upload (e.g. "device")
COMMONTAGVALUE = "boiler" # Value for the Tag specified above (e.g. "boiler")

# Enter influxdb settings below, or use a config file in user home directory
INFLUXCRED = {
    "Host" : "localhost",
    "Port" : 8086,
    "Username" : "",
    "Password" : "",
    "Database" : "",
    "Measurement" : ""
}

def create_json_stub (measurementName, tagkey, tagvalue):
    json_item = {}
    json_item.update({"measurement": measurementName})
    #json_item.update({"time": time})
    if tagkey != "" and tagvalue != "":
        json_item.update({"tags": {tagkey: tagvalue} })
    json_item.update({"fields": {} })
    return json_item

def clean_val(v):
    try:
        return float(v)
    except:
        return -9999

# looking for a config file in user home directory, if existing, use influx credentials from there 
influxcred_file = expanduser("~/.influxdb.credentials")
if exists(influxcred_file) :
    with open(influxcred_file, "r") as f:
        INFLUXCRED.update({k:v for k,v in json.loads(f.read()).items()})
# Because the influx credentials file can be used across multiple scripts, it is possible to specify a measurement to be used
# for the bsb2influx script. If specified, use it, otherwise use the general measurement.
if INFLUXCRED['Measurement_bsb2influx'] != "":
    INFLUXCRED['Measurement'] = INFLUXCRED['Measurement_bsb2influx']

client = InfluxDBClient(INFLUXCRED['Host'], INFLUXCRED['Port'], INFLUXCRED['Username'], INFLUXCRED['Password'], INFLUXCRED['Database'])

while (INTERVAL != -1):
    json_body = []
    json_item = create_json_stub (INFLUXCRED['Measurement'], COMMONTAG, COMMONTAGVALUE)
    url = "http://{}/JQ={}".format(ADAPTERADDRESS, FIELDS)
    r = requests.request(url=url, method="GET")
    if r.ok:
        j = r.json()
        for k in j:
            v = clean_val(j[k]["value"])
            if v != -9999:
                json_item['fields'].update({k: v })
        json_body.append(json_item)
        client.write_points(json_body)
        if VERBOSE:
            print("{0}".format(json_body))
    time.sleep(INTERVAL)

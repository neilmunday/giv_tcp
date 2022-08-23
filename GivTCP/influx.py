# version 2022.01.31
from influxdb_client import InfluxDBClient, WriteApi, WriteOptions
import logging
from logging.handlers import TimedRotatingFileHandler
from settings import GiV_Settings

if GiV_Settings.Log_Level.lower()=="debug":
    if GiV_Settings.Debug_File_Location=="":
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])
    else:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(),TimedRotatingFileHandler(GiV_Settings.Debug_File_Location, when='D', interval=1, backupCount=7)])
elif GiV_Settings.Log_Level.lower()=="info":
    if GiV_Settings.Debug_File_Location=="":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])
    else:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(),TimedRotatingFileHandler(GiV_Settings.Debug_File_Location, when='D', interval=1, backupCount=7)])
else:
    if GiV_Settings.Debug_File_Location=="":
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])
    else:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(),TimedRotatingFileHandler(GiV_Settings.Debug_File_Location, when='D', interval=1, backupCount=7)])


logger = logging.getLogger("GivTCP")

class GivInflux():

    def line_protocol(SN,readings):
        return '{},tagKey={} {}'.format(SN,'GivReal', readings) 

    def make_influx_string(datastr):
        new_str=datastr.replace(" ","_")
        new_str=new_str.lower()
        return new_str

    def publish(SN,data):
        output_str=""
        power_output = data['Power']['Power']
        for key in power_output:
            logging.info("Creating Power string for InfluxDB")
            output_str=output_str+str(GivInflux.make_influx_string(key))+'='+str(power_output[key])+','
        flow_output = data['Power']['Flows']
        for key in flow_output:
            logging.info("Creating Power Flow string for InfluxDB")
            output_str=output_str+str(GivInflux.make_influx_string(key))+'='+str(flow_output[key])+','
        energy_today = data['Energy']['Today']
        for key in energy_today:
            logging.info("Creating Energy/Today string for InfluxDB")
            output_str=output_str+str(GivInflux.make_influx_string(key))+'='+str(energy_today[key])+','

        energy_total = data['Energy']['Total']
        for key in energy_total:
            logging.info("Creating Energy/Total string for InfluxDB")
            output_str=output_str+str(GivInflux.make_influx_string(key))+'='+str(energy_total[key])+','

        logging.info("Data sent to Influx is: "+ output_str[:-1])
        data1=GivInflux.line_protocol(SN,output_str[:-1])
        
        _db_client = InfluxDBClient(url=GiV_Settings.influxURL, token=GiV_Settings.influxToken, org=GiV_Settings.influxOrg, debug=True)
        _write_api = _db_client.write_api(write_options=WriteOptions(batch_size=1))
        _write_api.write(bucket=GiV_Settings.influxBucket, record=data1)

        _write_api.close()
        _db_client.close()

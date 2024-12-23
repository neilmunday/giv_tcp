import argparse
import json
import re
import time

from prometheus_client import start_http_server
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, REGISTRY

import read as rd
from GivLUT import GivLUT

logger = GivLUT.logger


class GivTcpCollector:
    """
    Custom Prometheus exporter for GivTCP.
    """

    def collect(self):
        """
        Gather metrics from GivTCP.
        """
        logger.debug("Collecting metrics for export")

        battery_temp_re = re.compile(r"^Battery_Cell_(?P<cell>[0-9]+)_Temperature$")
        result = json.loads(rd.pubFromPickle())

        if "Battery_Details" in result:
            battery_labels = ["Serial"]
            battery_capacity_total_gauge = GaugeMetricFamily("battery_capacity_total", "Battery capacity total", labels=battery_labels)
            battery_capacity_remaining_gauge = GaugeMetricFamily("battery_capacity_remaining", "Battery capacity remaining", labels=battery_labels)
            battery_capacity_percentage_gauge = GaugeMetricFamily("battery_capacity_percentage", "Battery capacity remaining as a percentage", labels=battery_labels)
            battery_cell_temperature_gauge = GaugeMetricFamily("battery_cell_temperature", "Battery cell temperature", labels=["Serial", "Cell"])
            battery_voltage_gauge = GaugeMetricFamily("battery_voltage", "Battery voltage", labels=battery_labels)
            battery_temperature_gauge = GaugeMetricFamily("battery_temperature", "Battery temperature", labels=battery_labels)
            battery_cycles_counter = CounterMetricFamily("battery_cyles", "Number of battery cycle", labels=battery_labels)

            for serial, battery in result["Battery_Details"].items():
                capacity_percent = battery["Battery_Remaining_Capacity"] / battery["Battery_Design_Capacity"]
                if capacity_percent > 1:
                    capacity_percent = 1
                battery_cycles_counter.add_metric([serial], battery["Battery_Cycles"])
                battery_capacity_total_gauge.add_metric([serial], battery["Battery_Design_Capacity"])
                battery_capacity_remaining_gauge.add_metric([serial], battery["Battery_Remaining_Capacity"])
                battery_capacity_percentage_gauge.add_metric([serial], f"{capacity_percent:.03f}")
                battery_temperature_gauge.add_metric([serial], battery["Battery_Temperature"])
                battery_voltage_gauge.add_metric([serial], battery["Battery_Voltage"])

                for key, value in battery.items():
                    temp_match = battery_temp_re.match(key)
                    if temp_match:
                        cell = temp_match.group("cell")
                        battery_cell_temperature_gauge.add_metric([serial, cell], value)

            yield battery_cycles_counter
            yield battery_capacity_total_gauge
            yield battery_capacity_remaining_gauge
            yield battery_capacity_percentage_gauge
            yield battery_cell_temperature_gauge
            yield battery_temperature_gauge
            yield battery_voltage_gauge

        if "Invertor_Details" in result:
            yield GaugeMetricFamily("invertor_temperature", "Invertor temperature", value=result["Invertor_Details"]["Invertor_Temperature"])

        if "Power" in result:
            if "Flows" in result["Power"]:
                power_flow_gauge = GaugeMetricFamily("power_flow", "Power flow", labels=["Flow"])
                for flow, value in result["Power"]["Flows"].items():
                    power_flow_gauge.add_metric([flow], value)
                yield power_flow_gauge

            if "Power" in result["Power"]:
                yield GaugeMetricFamily("charge_time_remaining", "Charge time remaining", value=result["Power"]["Power"]["Charge_Time_Remaining"])
                yield GaugeMetricFamily("discharge_time_remaining", "Discharge time remaining", value=result["Power"]["Power"]["Discharge_Time_Remaining"])
                yield GaugeMetricFamily("grid_voltage", "Grid voltage", value=result["Power"]["Power"]["Grid_Voltage"])
                yield GaugeMetricFamily("soc", "State of charge", value=result["Power"]["Power"]["SOC"])

                power_gauage = GaugeMetricFamily("power", "Power", labels=["Metric"])
                power_re = re.compile(r"^(?P<metric>[\w]+)_Power$")

                for key, value in result["Power"]["Power"].items():
                    power_match = power_re.match(key)
                    if power_match:
                        metric = power_match.group("metric")
                        power_gauage.add_metric([metric], value)

                yield power_gauage

        if "Energy" in result:
            if "Rates" in result["Energy"]:
                yield GaugeMetricFamily("Current_Rate", "Current Rate", value=result["Energy"]["Rates"]["Current_Rate"])
                yield GaugeMetricFamily("Export_Rate", "Export Rate", value=result["Energy"]["Rates"]["Export_Rate"])
            if "Total" in result["Energy"]:
                yield CounterMetricFamily("AC_Charge_Energy_Total_kWh", "AC Charge_Energy Total kWh", value=result["Energy"]["Total"]["AC_Charge_Energy_Total_kWh"])
                yield CounterMetricFamily("Battery_Charge_Energy_Total_kWh", "Battery Charge_Energy Total kWh", value=result["Energy"]["Total"]["Battery_Charge_Energy_Total_kWh"])
                yield CounterMetricFamily("Battery_Discharge_Energy_Total_kWh", "Battery Discharge_Energy Total kWh", value=result["Energy"]["Total"]["Battery_Discharge_Energy_Total_kWh"])
                yield CounterMetricFamily("Battery_Throughput_Total_kWh", "Battery Throughput Total kWh", value=result["Energy"]["Total"]["Battery_Throughput_Total_kWh"])
                yield CounterMetricFamily("Export_Energy_Total_kWh", "Export Energy Total kWh", value=result["Energy"]["Total"]["Export_Energy_Total_kWh"])
                yield CounterMetricFamily("Import_Energy_Total_kWh", "Import Energy Total kWh", value=result["Energy"]["Total"]["Import_Energy_Total_kWh"])
                yield CounterMetricFamily("Invertor_Energy_Total_kWh", "Invertor Energy Total kWh", value=result["Energy"]["Total"]["Invertor_Energy_Total_kWh"])
                yield CounterMetricFamily("Load_Energy_Total_kWh", "Load Energy Total kWh", value=result["Energy"]["Total"]["Load_Energy_Total_kWh"])
                yield CounterMetricFamily("PV_Energy_Total_kWh", "PV Energy Total kWh", value=result["Energy"]["Total"]["PV_Energy_Total_kWh"])
                yield CounterMetricFamily("Self_Consumption_Energy_Total_kWh", "Self Consumption Energy Total kWh", value=result["Energy"]["Total"]["Self_Consumption_Energy_Total_kWh"])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Provides Prometheus metrics for GivTCP', add_help=True)
    parser.add_argument('-p', '--port', help='Specify the port to listen on', dest='port', type=int, default=9111)
    args = parser.parse_args()

    start_http_server(args.port)
    REGISTRY.register(GivTcpCollector())
    while True:
        time.sleep(1)

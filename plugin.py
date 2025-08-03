"""
<plugin key="MarstekCT" name="Marstek CT Meter" version="1.0" author="Haaibaai">
    <description>
        <h2>Marstek CT Meter plugin voor Domoticz</h2>
        <p>Deze plugin haalt data op van de Marstek CT meter via UDP.</p>
    </description>
    <params>
        <param field="Address" label="IP Adres CT Meter" width="200px" required="true" default="10.0.0.37"/>
        <param field="Mode1" label="Device Type" width="100px" required="true" default="HMG-50"/>
        <param field="Mode2" label="Battery MAC" width="150px" required="true" default="acd929a739fd"/>
        <param field="Mode3" label="CT MAC" width="150px" required="true" default="009b08069c30"/>
        <param field="Mode4" label="CT Type" width="100px" required="true" default="HME-3"/>
        <param field="Mode5" label="Refresh interval (sec)" width="75px" required="true" default="60"/>
    </params>
</plugin>
"""

import Domoticz
import socket
import time
import os
import json

COUNTER_FILE = os.path.join(os.path.dirname(__file__), "energy_totals.json")

# --- Marstek API klasse ---
class MarstekCtApi:
    def __init__(self, host, device_type, battery_mac, ct_mac, ct_type):
        self._host = host
        self._port = 12345
        self._device_type = device_type
        self._battery_mac = battery_mac
        self._ct_mac = ct_mac
        self._ct_type = ct_type
        self._timeout = 5.0
        self._payload = self._build_payload()

    def _build_payload(self):
        SOH, STX, ETX, SEPARATOR = 0x01, 0x02, 0x03, '|'
        message_fields = [self._device_type, self._battery_mac, self._ct_type, self._ct_mac, '0', '0']
        message_bytes = (SEPARATOR + SEPARATOR.join(message_fields)).encode('ascii')
        base_size = 1 + 1 + len(message_bytes) + 1 + 2
        total_length = base_size + len(str(base_size + 2))
        if len(str(total_length)) != len(str(base_size + 2)):
            total_length = base_size + len(str(total_length))
        payload = bytearray([SOH, STX])
        payload.extend(str(total_length).encode('ascii'))
        payload.extend(message_bytes)
        payload.append(ETX)
        xor = 0
        for b in payload:
            xor ^= b
        payload.extend(f"{xor:02x}".encode('ascii'))
        return payload

    def _decode_response(self, data: bytes):
        try:
            message = data[4:-3].decode('ascii')
        except UnicodeDecodeError:
            return {"error": "Invalid ASCII encoding"}
        fields = message.split('|')[1:]

        labels = [
            "meter_dev_type", "meter_mac_code", "hhm_dev_type", "hhm_mac_code",
            "A_phase_power", "B_phase_power", "C_phase_power", "A_charge_power", 
            "B_charge_power", "C_charge_power", "total_power", "A_discharge_power", 
            "B_discharge_power", "C_discharge_power", "Total_charge_power", "Total_discharge_power",
            "A_chrg_nb", "B_chrg_nb", "C_chrg_nb", "ABC_chrg_nb", "wifi_rssi",
            "info_idx", "x_chrg_power", "A_chrg_power", "B_chrg_power", "C_chrg_power",
            "ABC_chrg_power", "x_dchrg_power", "A_dchrg_power", "B_dchrg_power",
            "C_dchrg_power", "ABC_dchrg_power"
        ]

        parsed = {}
        for i, label in enumerate(labels):
            val = fields[i] if i < len(fields) else None
            try:
                parsed[label] = int(val)
            except (ValueError, TypeError):
                parsed[label] = val
        return parsed

    def fetch_data(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)
        try:
            sock.sendto(self._payload, (self._host, self._port))
            response, _ = sock.recvfrom(1024)
            return self._decode_response(response)
        except socket.timeout:
            return {"error": "Timeout - No response from meter"}
        except Exception as e:
            Domoticz.Error(f"Unexpected error in fetch_data: {str(e)}")
            return {"error": str(e)}
        finally:
            sock.close()

# --- Domoticz plugin class ---
class BasePlugin:
    def __init__(self):
        self.api = None
        self.host = None
        self.device_type = None
        self.battery_mac = None
        self.ct_mac = None
        self.ct_type = None
        self.refresh_interval = 60  # default
        self.last_update = 0

    def load_energy_totals(self):
        try:
            with open(COUNTER_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_power": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}

    def save_energy_totals(self, totals):
        with open(COUNTER_FILE, "w") as f:
            json.dump(totals, f)

    def onStart(self):
        Domoticz.Log("Marstek plugin gestart")
        self.host = Parameters["Address"]
        self.device_type = Parameters["Mode1"]
        self.battery_mac = Parameters["Mode2"]
        self.ct_mac = Parameters["Mode3"]
        self.ct_type = Parameters["Mode4"]
        self.refresh_interval = int(Parameters["Mode5"])

        self.api = MarstekCtApi(self.host, self.device_type, self.battery_mac, self.ct_mac, self.ct_type)

        if len(Devices) == 0:
            # Maak devices aan in Domoticz (voorbeeld)
            Domoticz.Device(Name="Total Power", Unit=1, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="A Phase Power", Unit=2, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="B Phase Power", Unit=3, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="C Phase Power", Unit=4, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="A Charge Power", Unit=5, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="B Charge Power", Unit=6, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="C Charge Power", Unit=7, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="A Discharge Power", Unit=8, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="B Discharge Power", Unit=9, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="C Discharge Power", Unit=10, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="Total Charge Power", Unit=11, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="Total Discharge Power", Unit=12, Type=248, Subtype=1).Create()
        if len(Devices) < 14:
            Domoticz.Device(Name="ABC Charge Power", Unit=13, Type=248, Subtype=1).Create()
            Domoticz.Device(Name="ABC Discharge Power", Unit=14, Type=248, Subtype=1).Create()
            
    def onHeartbeat(self):
        now = time.time()
        if now - self.last_update >= self.refresh_interval:
            data = self.api.fetch_data()
            
            Domoticz.Log("Data ontvangen van Marstek:")
            Domoticz.Log(str(data))
            
            if "error" in data:
                Domoticz.Error(f"Fout bij ophalen data: {data['error']}")
                return

            # Bereken verbruik (kWh)
            current_time = time.time()
            if not hasattr(self, 'last_heartbeat_time'):
                self.last_heartbeat_time = current_time

            delta_t = current_time - self.last_heartbeat_time
            self.last_heartbeat_time = current_time

            # Tijd in uren
            delta_hours = delta_t / 3600.0

            # Laad opgeslagen totals
            totals = self.load_energy_totals()

            # Accumuleer kWh = (Watt * uren) / 1000
            totals["total_power"] += data["total_power"] * delta_hours / 1000.0
            totals["A"] += data["A_phase_power"] * delta_hours / 1000.0
            totals["B"] += data["B_phase_power"] * delta_hours / 1000.0
            totals["C"] += data["C_phase_power"] * delta_hours / 1000.0

            # Opslaan
            self.save_energy_totals(totals)
           
            # Update Domoticz devices met data (voorbeeld)
            if 1 in Devices:
                Devices[1].Update(nValue=0, sValue=f"{data['total_power']};{totals['total_power']:.3f}")
            if 2 in Devices:
                Devices[2].Update(nValue=0, sValue=f"{data['A_phase_power']};{totals['A']:.3f}")
            if 3 in Devices:
                Devices[3].Update(nValue=0, sValue=f"{data['B_phase_power']};{totals['B']:.3f}")
            if 4 in Devices:
                Devices[4].Update(nValue=0, sValue=f"{data['C_phase_power']};{totals['C']:.3f}")
            if 5 in Devices:
                Devices[5].Update(nValue=0, sValue=str(data.get("A_charge_power", 0)))
            if 6 in Devices:
                Devices[6].Update(nValue=0, sValue=str(data.get("B_charge_power", 0)))
            if 7 in Devices:
                Devices[7].Update(nValue=0, sValue=str(data.get("C_charge_power", 0)))
            if 8 in Devices:
                Devices[8].Update(nValue=0, sValue=str(data.get("A_discharge_power", 0)))
            if 9 in Devices:
                Devices[9].Update(nValue=0, sValue=str(data.get("B_discharge_power", 0)))
            if 10 in Devices:
                Devices[10].Update(nValue=0, sValue=str(data.get("C_discharge_power", 0)))
            if 11 in Devices:
                Devices[11].Update(nValue=0, sValue=str(data.get("Total_charge_power", 0)))
            if 12 in Devices:
                Devices[12].Update(nValue=0, sValue=str(data.get("Total_discharge_power", 0)))
            if 14 in Devices:
                # === CHARGE POWER ===
                abc_chrg_mwh = data.get("ABC_chrg_power", 0)
                abc_chrg_kwh = abc_chrg_mwh / 1_000_000
                abc_chrg_nb = data.get("ABC_chrg_nb", 0)
                Devices[13].Update(nValue=0, sValue=f"{abc_chrg_nb};{abc_chrg_kwh:.3f}")
                Domoticz.Log(f"ABC Charge: {abc_chrg_nb} W / {abc_chrg_kwh:.3f} kWh")
                # === DISCHARGE POWER ===
                abc_dchrg_mwh = data.get("ABC_dchrg_power", 0)
                abc_dchrg_kwh = abc_dchrg_mwh / 1_000_000 if abc_dchrg_mwh else 0
                abc_dchrg_nb = data.get("ABC_dchrg_nb", 0) or 0  # Voor als deze ontbreekt
                Devices[14].Update(nValue=0, sValue=f"{abc_dchrg_nb};{abc_dchrg_kwh:.3f}")
                Domoticz.Log(f"ABC Discharge: {abc_dchrg_nb} W / {abc_dchrg_kwh:.3f} kWh")
    
            self.last_update = now
            Domoticz.Log("Data bijgewerkt")

# --- Globale plugin instantie ---
global _plugin
_plugin = BasePlugin()

def onStart():
    _plugin.onStart()

def onStop():
    pass

def onConnect():
    pass

def onMessage():
    pass

def onCommand(Unit, Command, Level, Color):
    pass

def onNotification():
    pass

def onDisconnect():
    pass

def onHeartbeat():
    _plugin.onHeartbeat() 

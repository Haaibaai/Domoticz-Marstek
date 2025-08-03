Features

This integration brings your Marstek CT Meter into Domoticz with a focus on ease of use and local control.

    💻 UI Configuration: No YAML needed for setup! Add and configure your meter directly through the Domoticz user interface.
    📡 Local Polling: All data is fetched directly from your device via UDP on your local network. No cloud connection is required.
    🏠 Automatic Device & Entities: Creates devices in Domoticz and automatically adds all relevant sensors.
    📊 Key Sensors: Provides sensors for Total Power and Phase A/B/C Power.
    
⚠️ Disclaimer

This is an independent, community-developed integration and is not officially affiliated with or endorsed by Marstek or Hame. It was created based on publicly available information and community research. Use at your own risk.
📋 Prerequisites

Before you can install and configure this integration, please ensure you have the following:

    Hardware:
        A supported Marstek CT Smart Meter (tested with CT003).
        A local Wi-Fi network the meter is connected to.

    Domoticz
        A working Domoticz instance.
        Plug in support
        
    Required Information:
        IP Address: The local IP Address of your CT meter.
        Battery & CT Meter MAC: These are special 12-character MAC addresses found within the official Marstek mobile app under "Device Management".
            Format: A 12-character hexadecimal string without colons or dashes.
            Important: These are NOT the network MAC addresses that your router sees.
        Device & CT Types: These are typically pre-filled correctly.
            Device Type HMG-50: Corresponds to the Marstek Venus E 5.12.
            CT Type HME-4: Corresponds to the CT002.
            CT Type HME-3: Corresponds to the CT003.

🚀 Installation

Create a plugin directory
Extract all files there
Restart Domoticz
Find Marstek in the list of Hardware and fill in the details
    
🙏 Acknowledgements

This integration would not have been possible without the foundational work and protocol analysis by R. Weijnen (https://github.com/rweijnen) and D-shmt (https://github.com/d-shmt/hass_marstek-smart-meter)

    Original Research: rweijnen/marstek-venus-e-firmware-notes

💬 Feedback & Contributions
If you encounter any issues or have suggestions for improvements, please open an issue on this GitHub repository. Contributions are always welcome!

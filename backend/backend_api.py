#new
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI backend!"}

api_url = 'https://device-services-maya.gentleplant-8ec40f17.centralindia.azurecontainerapps.io/api/device-service/v2/c09b7257-2c61-4854-8461-f9f8abeb6a68/device_management/fetch_chart_data'


class RequestData(BaseModel):
    deviceSerialNumber: str
    type: str = "modon"
    data_per_page: int

# Function to fetch data from the main API with dynamic serial number
async def fetch_data(deviceSerialNumber: str, dataPerPage: int):
    request_data = {
        "deviceSerialNumber": deviceSerialNumber,
        "type": "modon",
        "data_per_page": dataPerPage,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=request_data)
            response.raise_for_status()
            data = response.json()
            return data['response']['Payload']  # Return the full payload
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


@app.get("/api/{device_serial}/energymeterdata")
async def get_energy_meter_data(device_serial: str, data_per_page: int = 1):
    payload = await fetch_data(device_serial, data_per_page)

    if not payload:
        raise HTTPException(status_code=500, detail="Failed to fetch data")

    # Filter out empty or invalid records
    valid_payload = [record for record in payload if record and 'property' in record]

    # Extract and transform the data into the requested format
    transformed_data = []
    for record in valid_payload:
        device_data = record.get('property', {})
        timestamp = record.get('created_at', None)
        date = timestamp.split('T')[0] if timestamp else None
        time = timestamp.split('T')[1].split('.')[0] if timestamp else None

        transformed_data.append({
            "energyMeterdata": {
                "DVer": "Version 1.0",
                "PVer": "Version 1.0",
                "deviceID": device_data.get("serial number", None),
                "deviceCategory": "Energy Meter",
                "sourceSitename": None,
                "date": date,
                "time": time,
                "modelName": device_data.get("modelname", None),
                "deviceName": device_data.get("devicename", None),
                "version": device_data.get("version", None),
                "macAddress": device_data.get("mac address", None),
                "serialNumber": device_data.get("serial number", None),
                "IPADD": device_data.get("IPADD", None),
                "status": device_data.get("status", None),
                "voltage": {
                    "V1": device_data.get("V1_Voltage", None),
                    "V2": device_data.get("V2_Voltage", None),
                    "V3": device_data.get("V3_Voltage", None),
                },
                "current": {
                    "I1": device_data.get("I1_Current", None),
                    "I2": device_data.get("I2_Current", None),
                    "I3": device_data.get("I3_Current", None),
                },
                "power": {
                    "KW": {
                        "L1": device_data.get("KW_L1", None),
                        "L2": device_data.get("KW_L2", None),
                        "L3": device_data.get("KW_L3", None),
                    },
                    "Kvar": {
                        "L1": device_data.get("Kvar_L1", None),
                        "L2": device_data.get("Kvar_L2", None),
                        "L3": device_data.get("Kvar_L3", None),
                    },
                    "KVA": {
                        "L1": device_data.get("KVA_L1", None),
                        "L2": device_data.get("KVA_L2", None),
                        "L3": device_data.get("KVA_L3", None),
                    },
                    "PF": {
                        "L1": device_data.get("PF_L1", None),
                        "L2": device_data.get("PF_L2", None),
                        "L3": device_data.get("PF_L3", None),
                    },
                    "Total": {
                        "Kvar": device_data.get("Total_Kvar", None),
                        "KVA": device_data.get("Total_KVA", None),
                        "PF": device_data.get("Total_PF", None),
                        "KW": device_data.get("Total_KW", None),
                    },
                },
                "energy": {
                    "KwhImport": device_data.get("Kwh_Import", None),
                    "KVAhImport": device_data.get("KVAh_import", None),
                },
                "network": {
                    "act": device_data.get("act", None),
                    "rssi": device_data.get("rssi", None),
                    "wwanIp": device_data.get("wwan_ip", None),
                    "rsrp": device_data.get("rsrp", None),
                    "rsrq": device_data.get("rsrq", None),
                    "lte": {
                        "rx": device_data.get("lte_rx", None),
                        "tx": device_data.get("lte_tx", None),
                        "bytes": device_data.get("lte_bytes", None),
                    },
                },
            }
        })

    return transformed_data

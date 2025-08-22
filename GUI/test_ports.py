import ctypes
from ctypes import wintypes
import wmi

# Librería cfgmgr32
_cfg = ctypes.WinDLL("CfgMgr32")
CR_SUCCESS = 0
CM_LOCATE_DEVNODE_NORMAL = 0x00000000
CM_DRP_BUSREPORTEDDEVICE_DESC = 22
CM_DRP_DEVICEDESC = 1  # Descripción del dispositivo
CM_DRP_HARDWAREID = 2  # Hardware ID
CM_DRP_FRIENDLYNAME = 13  # Nombre amigable
CM_DRP_LOCATION_INFORMATION = 14  # Información de ubicación
CM_DRP_MFG = 12  # Fabricante

# Firmas de las funciones
_cfg.CM_Locate_DevNodeW.argtypes = [ctypes.POINTER(
    wintypes.ULONG), wintypes.LPCWSTR, wintypes.ULONG]
_cfg.CM_Locate_DevNodeW.restype = wintypes.ULONG

# Usar el nombre correcto de la función
_cfg.CM_Get_DevNode_Registry_PropertyW.argtypes = [
    wintypes.ULONG,      # DEVINST dnDevInst
    wintypes.ULONG,      # ULONG ulProperty (22)
    ctypes.POINTER(wintypes.ULONG),  # pulRegDataType
    wintypes.LPVOID,     # Buffer
    ctypes.POINTER(wintypes.ULONG),  # pulLength
    wintypes.ULONG       # ulFlags
]
_cfg.CM_Get_DevNode_Registry_PropertyW.restype = wintypes.ULONG


def get_device_property(pnp_id, property_code):
    """Función general para obtener propiedades de dispositivos"""
    try:
        # 1) Localizar DEVINST
        devinst = wintypes.ULONG()
        ret = _cfg.CM_Locate_DevNodeW(
            ctypes.byref(devinst),
            pnp_id,
            CM_LOCATE_DEVNODE_NORMAL
        )
        if ret != CR_SUCCESS:
            return f"Error localizando dispositivo: 0x{ret:08X}"

        # 2) Primero obtener el tamaño requerido del buffer
        buf_len = wintypes.ULONG(0)
        data_type = wintypes.ULONG()
        
        # Llamar primero con buffer NULL para obtener el tamaño requerido
        ret = _cfg.CM_Get_DevNode_Registry_PropertyW(
            devinst.value,
            property_code,
            ctypes.byref(data_type),
            None,  # Buffer NULL para obtener tamaño
            ctypes.byref(buf_len),
            0
        )
        
        # Códigos de error comunes que no son fatales
        if ret == 0x1A:  # CR_NO_SUCH_VALUE - La propiedad no existe
            return "N/A"
        elif ret == 0x0D:  # CR_NO_SUCH_DEVINST - El dispositivo no existe
            return "Dispositivo no encontrado"
        elif ret != 0x25:  # CR_BUFFER_SMALL - El único error esperado
            return f"Error: 0x{ret:08X}"
        
        # 3) Ahora crear buffer con el tamaño correcto y obtener los datos
        if buf_len.value > 0:
            buf = ctypes.create_unicode_buffer(buf_len.value // 2)  # Dividir por 2 porque es Unicode
            ret = _cfg.CM_Get_DevNode_Registry_PropertyW(
                devinst.value,
                property_code,
                ctypes.byref(data_type),
                buf,
                ctypes.byref(buf_len),
                0
            )
            if ret != CR_SUCCESS:
                return f"Error leyendo datos: 0x{ret:08X}"
            return buf.value
        else:
            return "Sin datos"
    
    except Exception as e:
        return f"Excepción: {str(e)}"


def get_all_device_info(pnp_id):
    """Obtiene toda la información disponible del dispositivo"""
    info = {}
    properties = {
        'Descripción': CM_DRP_DEVICEDESC,
        'Nombre Amigable': CM_DRP_FRIENDLYNAME,
        'Hardware ID': CM_DRP_HARDWAREID,
        'Fabricante': CM_DRP_MFG,
        'Ubicación': CM_DRP_LOCATION_INFORMATION,
        'Bus Reported': CM_DRP_BUSREPORTEDDEVICE_DESC
    }
    
    for name, prop_code in properties.items():
        info[name] = get_device_property(pnp_id, prop_code)
    
    return info


def bus_reported_desc_from_pnpid(pnp_id):
    """Función original mantenida para compatibilidad"""
    return get_device_property(pnp_id, CM_DRP_BUSREPORTEDDEVICE_DESC)


# Ejemplo de uso: listar todos los COM con toda su información
c = wmi.WMI()
for sp in c.Win32_SerialPort():
    # sp.DeviceID -> "COM3", sp.PNPDeviceID -> "USB\VID_0403&PID_6001\A6008___"
    device_info = get_all_device_info(sp.PNPDeviceID)
    
    # Obtener también información de WMI
    wmi_info = []
    if hasattr(sp, 'Description') and sp.Description:
        wmi_info.append(f"WMI Descripción: {sp.Description}")
    if hasattr(sp, 'Name') and sp.Name:
        wmi_info.append(f"WMI Nombre: {sp.Name}")
    if hasattr(sp, 'Caption') and sp.Caption:
        wmi_info.append(f"WMI Caption: {sp.Caption}")
    
    # Crear la cadena de descripción con todos los datos disponibles
    descriptions = []
    
    # Agregar información del registro de Windows
    for name, value in device_info.items():
        if value and value != "N/A" and value != "Sin datos" and not value.startswith("Error"):
            descriptions.append(f"{name}: {value}")
    
    # Agregar información de WMI
    descriptions.extend(wmi_info)
    
    # Siempre mostrar el PNP Device ID como referencia
    descriptions.append(f"PNP ID: {sp.PNPDeviceID}")
    
    description_str = " | ".join(descriptions) if descriptions else "Sin información disponible"
    
    print(f"{sp.DeviceID}: {description_str}")

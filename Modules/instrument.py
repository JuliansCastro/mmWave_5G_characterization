'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)
- Juan Felipe González Pardo        (jugonzalezpa@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of controlling the R&S RF generator 
                and the spectrum analyzer.
'''



import contextlib
import time
import numpy as np
from RsInstrument import *
from queue import LifoQueue, Full

''' Rohde & Schwarz instruments classes for communication and control '''
# R&S Instrument Controller - VISA Protocol
class Instrument:
    def __init__(self, instrument_ip, settings = None):
        self._instrument = None
        self._connected = False
        self._stream = True
        if settings is None:
            self._instrument_ip = instrument_ip
            self._instrument_name = None 
        else:
            self._instrument_ip = settings["IP"]
            self._instrument_name = settings["Name"] 


        try: 
            self._instrument = RsInstrument(f"TCPIP::{self._instrument_ip}::inst0::INSTR")
            self._instrument.visa_timeout = 3000
            self._instrument_name = self._instrument.query_str('*IDN?')

            self._connected = True
            #self._instrument = pyvisa.ResourceManager().open_resource("TCPIP::"+self._instrument_ip+"::inst0::INSTR")
            #self._instrument.timeout = 5000
            #self._instrument_name = self._instrument.query('*IDN?')
            #self._connected = True
        except Exception as e:
            print(e)
            print(f"Failed connection with the {self._instrument_ip} instrument.")
        
    @property
    def instrument(self):
        return self._instrument
    
    @property
    def instrument_ip(self):
        return self._instrument_ip

    @property
    def instrument_name(self):
        return self._instrument_name
    
    @property
    def connected(self):
        return self._connected
    
    @property
    def stream(self):
        return self._stream
    
    @stream.setter
    def stream(self, start_stop):
        self._stream = start_stop

''' RF Generator '''
class RSGenerator(Instrument):
    
    POWER_RANGE = [-100, 25]
    FREQUENCY_RANGE = [400e3, 6e9]

    def __init__(self, ip = "", power = -50, frequency = 2e9, limiter = 25, settings = None):
        super().__init__(ip, settings = settings)
        if self._connected:
            self._generator = self._instrument
            self._generator.write("SOUR1:FREQ:MODE CW")
            self._generator_ip = self._instrument_ip
            self._generator_name = self._instrument_name
            

            if settings is None:
                self.power = power
                self.frequency = frequency
                self.limiter = limiter
            else:
                self.power = settings["Settings"]["Power"]
                self.frequency = settings["Settings"]["Frequency"]
                self.limiter = settings["Settings"]["Limiter"]
            
            self.new_frequency = frequency
            self.new_power = power
            
            self._status = "Off"
            self._q = LifoQueue(maxsize=2)
            self.off
            self._stream = True 
            self.print_configuration()    


    @property
    def power(self):
        return self._power
    

    @property
    def frequency(self):
        return self._frequency
    
    @property
    def status(self):
        return self._status
    
    @property
    def q(self):
        return self._q

    @property
    def preset(self):
        self._generator.write("SYST:PRES")

    @power.setter
    def power(self, power):
        self._power = power
        self._generator.write_float("SOUR1:POW:POW ", power)  
        time.sleep(0.2)      
    
    @frequency.setter
    def frequency(self, frequency):
        self._frequency = frequency
        self._generator.write_float("SOUR1:FREQ:CW ", frequency)
        time.sleep(0.5)

    @property
    def on(self):
        self._status = "On"
        self._generator.write("OUTP1:STAT ON")
    
    @property
    def off(self):
        self._status = "Off"
        self._generator.write("OUTP1:STAT OFF")
        self._generator.write("SOURce1:BB:ARBitrary:STATe OFF")

    def print_configuration(self):

        print("\n**************************************************")
        print("|             Generator Information               |")
        print("**************************************************")
        print("Generator:")
        print("  Name :          %s"% self.instrument_name)
        print("  IP Address:     %s"% self.instrument_ip)
        
        print("Generator Configuration:")
        print("  Frequency:       %f MHz"% self.frequency)        
        print("  Server:          %s "% self.power)
        print("  Output Power:    %f dBm"% self.power)
        print("  Limiter Power:   %f dBm"% self.limiter)

    def list(self,frequency,power,dwell):
        self.simulationTime = 2*dwell[0]*1e-6*len(frequency)
        self._generator.write("SOUR1:LIST:SEL '/var/user/list1.lsw'")
        self._generator.write("SOUR1:LIST:FREQ "+str(frequency.tolist()).lstrip('[').rstrip(']'))
        self._generator.write("SOUR1:LIST:POW "+str(power.tolist()).lstrip('[').rstrip(']'))
        self._generator.write("SOUR1:LIST:DWEL:LIST "+str(dwell.tolist()).lstrip('[').rstrip(']'))
        self._generator.write("SOUR1:LIST:MODE AUTO")
        self._generator.write("SOUR1:LIST:TRIG:SOUR AUTO")
        self._generator.write("SOUR1:LIST:DWEL:MODE LIST")
        self._generator.write("OUTP1:STAT ON")
        self._generator.write("SOUR1:FREQ:MODE LIST")

        # --------------- Command to start with the measurement on the raspberry -----------------------
        print(f"Simulation time: {str(self.simulationTime)}s")
        time.sleep(self.simulationTime)
        # --------------- Command to stop with measurement on the raspberry ----------------------

        self._generator.write("SOUR1:FREQ:MODE CW")
        self._generator.write("OUTP1:STAT OFF")
        time.sleep(1)

    def singleTone(self, frequency, power): 
        self._generator.write("SOUR1:FREQ:MODE CW")
        self._generator.write_float("SOUR1:FREQ:CW ", frequency)
        self._generator.write_float("SOUR1:POW:POW ", power)
    
    def multiCarrier(self,carries,spacing):
        self.carries = carries
        self.spacing = spacing
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:PRESet")
        time.sleep(1)
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CARRier:MODE EQU")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CARRIer:COUNt "+str(self.carries))
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CARRIer:SPACing "+str(self.spacing))
        for i in range(carries):
            self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CARRier"+str(i+1)+":STATe ON")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CFACtor:MODE MAX")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CLIPping:CFACtor 50")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CLIPping:STATe ON")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:TIME:MODE LCM")
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:POWer:REFerence RMS")
        self._generator.write('SOURce1:BB:ARBitrary:MCARrier:OFILe "Example"')
        time.sleep(1)
        self._generator.write("SOURce1:BB:ARBitrary:MCARrier:CLOad")
        time.sleep(1)
        self._generator.write("SOURce1:BB:ARBitrary:STATe ON")
    
    def stream_thread(self):
        
        self.on

        while self._stream:
            

            if self.new_power != self._power:
                self.power = self.new_power
            if self.new_frequency != self._frequency:
                self.frequency = self.new_frequency*1e-6

            with contextlib.suppress(Full):
                self._q.put_nowait([self._power, self._frequency])
        self.off


# if __name__=='__main__':

#     generator = RSGenerator("172.177.75.22", power = -60, frequency = 500e6)

#     print('Turning on...')
#     generator.on
#     print('On:)')
#     rta = input('Enter key: ')
#     if rta is not None:
#         generator.off

class RSSpectrumAnalyzer(Instrument):

    #RANGE = [150, 130, 120, 100, 50, 30, 20, 10, 5, 3, 2, 1]

    SETTINGS = {
                # Start and stop frequencies of the horizontal axis of the diagram area, for more information 
                # about its settings refer to page 107 (109) of the user manual
                "START": 2200e6,
                "STOP": 2700e6, 

                "STEP": 200e3, # Frequency step size, for more information about its settings refer to page 105 (107) of the user manual
                "SPAN": 100e3, # Frequency range around the center frequency that a spectrum analyzer displays on the screen,
                # for more information about its settings refer to page 107 (109) of the user manual

                "RANGE": 80, # Determines the scaling or resolution of the vertical axis. For more information about its settings refer
                # to page 110 (112) of the user manual
                "RLEVEL": -10, # The reference level sets the input signal gain up to the display stage. If the reference level is
                # low, the gain is high. For more information about its settings refer to page 109 (111) of the user manual
                "ATTENUATION": 10, # RF attenuation adjusts the input range inside the analyzer. It is coupled directly to the
                # reference level. For more information about its settings refer to page 111 (113) of the user manual

                "RBW": 100e3, # The resolution bandwidth in a spectrum analyzer determines the frequency resolution
                # for frequency domain measurements and therefore determines how well it can separate adjacent frequencies.
                # For more information about its settings refer to page 112 (114) of the user manual

                #doesn't seem to be used
                "VBW": 10e3 # The video bandwidth (VBW) basically smoothes the trace by reducing the noise and therefore 
                # making power levels easier to see. For more information about its settings refer to page 115 (117) of the user manual
                }

    def __init__(self, ip, settings = None):
        super().__init__(ip, settings = settings)
        self._analyzer = self.instrument
        self.setting = True
        self._stream = True
        self._q = LifoQueue(maxsize=50)


        if settings is not None:
            self.SETTINGS = settings
        
    # Function meant to ensure that the SA is set to SA operation mode
    def set_inst_mode(self):
        print(f" Current mode: {self._analyzer.query_str('INSTrument:SELect?')}")
        if self._analyzer.query_str('INSTrument:SELect?') != "SAN":
            self._analyzer.write("INST SAN")
            self._analyzer.write("*WAI")
            time.sleep(1)
            print(f" Updated mode: {self._analyzer.query_str('INSTrument:SELect?')}")

    # Function to configure the analyzer with the defined settings        
    def set_instrument(self, update_scale = True):

        #self._analyzer.write("INST SAN")
        #self.set_inst_mode()
        self._analyzer.write("*WAI")
        
        # Configuring the Horizontal Axis
        self._analyzer.write("*RST") #RESET sets the instrument to a defined default status. The command essentially
        #corresponds to pressing the PRESET key
        self._analyzer.write("FREQuency:MODE SWE") # sets the frequency mode to Sweep mode, frequency domain (span > 0)
        self._analyzer.write_float("FREQuency:STARt ", self.SETTINGS["START"])
        self._analyzer.write_float("FREQuency:STOP ", self.SETTINGS["STOP"]),
        
        # Configuring the Vertical Axis
        self._analyzer.write("UNIT:POWer DBM") # sets the unit of vertical axis, DBM (dBm), DBUV (dBµV), DBMV (dBmV), W (Watt), V (Volt).
        self._analyzer.write_float("DISPlay:TRACe:Y ", self.SETTINGS["RANGE"]) #numeric value in the range from 10 dB to 200 dB
        self._analyzer.write_float("DISPlay:TRACe:Y:RLEV ", self.SETTINGS["RLEVEL"]) # sets the reference level for the vertical axis
        self._analyzer.write_int("DISPlay:TRACe:Y:RPOS ", 10) # defines the position of the reference level on the display grid.
        self._analyzer.write_int("INPut:ATTenuation ", self.SETTINGS["ATTENUATION"]) # Numeric value in the range from 0 dB to 40 dB in 5 dB steps
        self._analyzer.write_int("INPut:IMPedance ", 50)

        self._analyzer.write_float("BANDwidth ", self.SETTINGS["RBW"])
        self._analyzer.write("DETector POSitive")    # APEak | NEGative | POSitive | SAMPle | RMS
        #self._analyzer.write("UNIT:POWer DBM")
        #self._analyzer.write("SENS:BAND AUTO ON")
        #self._analyzer.write("SENS:VID AUTO ON")
        #self._analyzer.write("CALC:MARK:FUNC:STR ON") ## Set the mark in the maximum level
        #self._analyzer.write("CALC:MARK:FUNC:STR: BAND 5 E6")
        if update_scale:
            self.update_scale()

    def print_configuration(self):

        print("\n---------------------------------------")
        print("       Spectrum Analyzer settings")
        print("---------------------------------------\n")
        
        print(f" Frequency Mode:         {self._analyzer.query_str('SENSe:FREQuency:MODE?')}")
        print(f" Start Frequency:        {self._analyzer.query_float('FREQuency:STARt?')*1e-6} MHz")
        print(f" Stop Frequency:         {self._analyzer.query_float('FREQuency:STOP?')*1e-6} MHz")            
        print(f" Span:                   {self._analyzer.query_float('FREQuency:SPAN?')*1e-6} MHz")
        print(f" Bandwidth:              {self._analyzer.query_float('BANDwidth?')*1e-6} MHz")
        print(f" Detector:               {self._analyzer.query_str('DETector?')}")
        print(f" Attenuation:            {self._analyzer.query_int('INPut:ATTenuation?')}")
        print(f" Vertical axis units:            {self._analyzer.query_str('UNIT:POWer?')}")
        print(f" Vertical axis display range:            {self._analyzer.query_str('DISP:TRAC:Y?')}")
        #print(f" Trace Points:           {self._analyzer.query_str('TRACe:POINts? TRACE1')}")
        print("---------------------------------------")

    # Function meant to set the proper transducer to perform E-field magnitude measurements as well as other measurements depending on the probe
    def set_field_probe(self):
        """
            Meas
            Modo de medición
            Dirección Iso (Auto X, Y, Z)
            Amplitude
            Transductor
                Seleccionar transductor primario pasar los datos entre comillas 'Pag 46'

        """
        # Dictionary to store the installed transducer configurations, when using them the vertical axis units change by default to DUVM (dBµV/m), other available options include V_M (V/m) and W_M2 (W/m^2). For more info on transducers refer to page 142 (142) of the operation manual.
        TRANSDUCER =   {'TSEMF-B1':{'Auto': 'TSEMF-B1_typical.isotrd', 
                                  'X': '', 
                                  'Y': '', 
                                  'Z': ''},

                        'TSEMF-B2':{'Auto': 'TSEMF-B2_typical.isotrd', 
                                  'X': '', 
                                  'Y': '', 
                                  'Z': ''},

                        'TSEMF-B3':{'Auto': 'TSEMF-B3_typical.isotrd', 
                                    'X': 'TSEMF-B3_101784_X.pritrd', 
                                    'Y': 'TSEMF-B3_101784_Y.pritrd', 
                                    'Z': 'TSEMF-B3_101784_Z.pritrd'},

                        'EMF-B1':{'Auto': '', 
                                  'X': 'EMF_B1_101793_X.pritrd', 
                                  'Y': 'EMF_B1_101793_Y.pritrd', 
                                  'Z': 'EMF_B1_101793_Z.pritrd'}
                        }

        axis = "X"

        transducer = self._analyzer.query("CORR:TRAN:ISOT?")
        self._analyzer.write(f"CORRection:TRANsducer1:SELect '{TRANSDUCER['TSEMF-B3'][axis]}'")
        self._analyzer.write("CORRection:TRANsducer1 ON")
        self._analyzer.write(f"INPut:ANTenna:MEASure {axis}")
        self._analyzer.write("INPut:ANTenna:STATe ON")
        self.update_scale()
        
    # Function meant to adjust the limits of the vertical axis according to the measured maxima and minima of the spectre within the specified frequency range. Calling it implies ignoring the specified values for the reference level, the display range and the video bandwidth. Required to draw the test animation of the data shown in the spectrum analyzer   
    def update_scale(self):
        peak = self.get_peak()
        minimum = self.get_min()
        display_range = 4*np.abs(peak-minimum)
        if display_range > 150: # 150dB is the display limit for the FSH8 model
            display_range = 150
        ref_lvl=peak+5
        if ref_lvl > 20: # 20dBm is the maximum ref level for the FSH8 model
            ref_lvl = 20
        print(f"Minimum: {minimum}")
        print(f"Maximum: {peak}")
        self._analyzer.write_float("DISPlay:TRACe:Y ", display_range)
        self._analyzer.write_float("DISPlay:TRACe:Y:RLEV ", ref_lvl)
        self.y_range = (ref_lvl-display_range, ref_lvl)
        #self._analyzer.write_int("DISPlay:TRACe:Y:RPOS ", peak)  


    def set_trigger(self):
        pass
    
    def get_peak(self):
        peak_array=[]
        for _ in range(5):
            if self.setting:
                self._analyzer.write("CALCulate:MARKer:AOFF")
                self._analyzer.write("CALCulate:MARKer1 ON")
                
                self.setting = False
                time.sleep(.5)
            self._analyzer.write("CALCulate:MARKer1:MAX")

            peak_array.append( self._analyzer.query_float("CALCulate:MARKer1:Y?"))
            self.setting = True
        
        return np.max(np.array(peak_array)) # maximum value of the array

    def get_min(self):
        min_array = []
        for _ in range(5):
            if self.setting:
                self._analyzer.write("CALCulate:MARKer:AOFF")
                self._analyzer.write("CALCulate:MARKer1 ON")
                time.sleep(.5)
                self.setting = False
            self._analyzer.write("CALCulate:MARKer1:MIN")

            min_array.append( self._analyzer.query_float("CALCulate:MARKer1:Y?"))
            self.setting = True
        
        return np.min(np.array(min_array)) # minimum value of the array

    def get_trace(self):
        time.sleep(.2)
        return self._analyzer.query_bin_or_ascii_float_list("TRACe:DATA? TRACE1")      # The R&S FSH returns 631 values. Each value corresponds to one pixel of a trace # trace

    def stream_thread(self):
        while self._stream:
            
            with contextlib.suppress(Full):
                self._q.put_nowait(self.get_trace())
    
    
    """
    Meas
    Modo de medición
    Dirección Iso (Auto X, Y, Z)
    Amplitude
    Transductor
        Seleccionar transductor primario pasar los datos entre comillas 'Pag 46'


        """
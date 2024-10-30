'''
Develop by:

- Julián Andrés Castro Pardo        (juacastropa@unal.edu.co)
- Diana Sofía López                 (dialopez@unal.edu.co)
- Carlos Julián Furnieles Chipagra  (cfurniles@unal.edu.co)

  Wireless communications - Professor Javier L. Araque
  Master in Electronic Engineering
  UNAL - 2024-1

  Date: 2024-10-29


  Description:  This class is in charge of the acquisition of USRP data,
                it reads the serial port assigned to the USRP device and 
                parse the data to the required format (power in dbm).
'''



import uhd
import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class USRP:
    '''
    A class to interface with the USRP (Universal Software Radio Peripheral) device.

    This class provides methods to configure and control the USRP for both 
    receiving and transmitting signals. It allows for real-time data acquisition 
    and signal processing, making it suitable for various communication and research applications.

    Args:
        master_clock_rate (float): The master clock rate for the USRP, default is 20e6.
        rx_sample_rate (float): The sample rate for receiving signals, default is 2e6.
        rx_center_freq (float): The center frequency for receiving signals, default is 500e6.
        rx_gain (float): The gain for the receiver, default is 0.
        rx_num_samps (int): The number of samples to be received, default is 2^12.
        rx_buffer_length (int): The length of the receive buffer, default is 2^10.
        tx_sample_rate (float): The sample rate for transmitting signals, default is 2e6.
        tx_center_freq (float): The center frequency for transmitting signals, default is 500e6.
        tx_gain (float): The gain for the transmitter, default is 0.
        tx_buffer_length (int): The length of the transmit buffer, default is 2**10.
        z0 (float): The characteristic impedance, default is 50.
        channel_mapping (int): The channel mapping for the USRP, default is 0.

    Attributes:
        master_clock_rate (float): The master clock rate for the USRP.
        z0 (float): The characteristic impedance.
        channel_mapping (int): The channel mapping for the USRP.
        rx_sample_rate (float): The sample rate for receiving signals.
        rx_center_freq (float): The center frequency for receiving signals.
        rx_gain (float): The gain for the receiver.
        rx_num_samps (int): The number of samples to be received.
        rx_buffer_length (int): The length of the receive buffer.
        tx_sample_rate (float): The sample rate for transmitting signals.
        tx_center_freq (float): The center frequency for transmitting signals.
        tx_gain (float): The gain for the transmitter.
        tx_buffer_length (int): The length of the transmit buffer.
        rx_samples (numpy.ndarray): Array to hold received samples.
        rx_thread (threading.Thread): Thread for receiving samples.
        rx_continuous_sampling (bool): Flag for continuous sampling.
        _usrp (uhd.usrp.MultiUSRP): The USRP device instance.
    
    Methods
    --------
        printConfiguration() -> None:
            Display the current configuration settings of the USRP device.
        
        setReceiver() -> None:
            Configure the receiver settings for the USRP device.
        
        setReceiveBuffer() -> None:
            Initialize the receive buffer and streaming configuration for the USRP device.
        
        startRxStream() -> None:
            Start the continuous reception stream for the USRP device.
        
        stopRxStream() -> None:
            Stop the continuous reception stream for the USRP device.
        
        getSamples() -> numpy.ndarray:
            Retrieve a specified number of samples from the USRP receiver.
        
        getPower_dBm(samples: numpy.ndarray) -> float:
            Calculate the received power in decibels relative to one milliwatt (dBm).

        updateRxGain(new_gain: float) -> None:
            Dynamically update the receive gain of the USRP device.
        
        _continuousRxSampling() -> None:
            Continuously sample data from the USRP receiver while enabled.
        
        startRxThread() -> None:
            Initialize and start the receiver thread for continuous data sampling.
        
        stopRxThread() -> None:
            Stop the receiver thread and halt continuous data sampling.
        
        transmission(duration: float) -> None:
            Transmit a waveform signal using the USRP device.
        
        setTransmitter() -> None:
            Configure the transmitter settings for the USRP device.
        
        setTransmitterStreamer() -> None:
            Initialize the transmitter streamer configuration for the USRP device.
            
        sendSignal(signal: numpy.ndarray, tx_duration: float) -> None:
            Transmit a given signal using the USRP device for a specified duration
    '''
    def __init__(self, master_clock_rate = 20e6, rx_sample_rate = 2e6, 
                 rx_center_freq = 500e6, rx_gain = 0, rx_num_samps = 2**12,
                 rx_buffer_length = 2**10, tx_sample_rate = 2e6, tx_center_freq = 500e6,
                 tx_gain = 0, tx_buffer_length = 2**10,
                 z0 = 50, channel_mapping = 0) -> None:
        
        self.master_clock_rate = master_clock_rate
        self.z0 = z0
        self.channel_mapping = channel_mapping

        # Reception attributes
        self.rx_sample_rate = rx_sample_rate
        self.rx_center_freq = rx_center_freq
        self.rx_gain = rx_gain
        self.rx_num_samps = rx_num_samps
        self.rx_buffer_length = rx_buffer_length

        # Transmission attributes
        self.tx_sample_rate = tx_sample_rate
        self.tx_center_freq = tx_center_freq
        self.tx_gain = tx_gain
        #self.tx_num_samps = tx_num_samps
        self.tx_buffer_length = tx_buffer_length

        # Attributes needed for threading
        self.rx_samples = np.zeros(self.rx_num_samps, dtype=np.complex64)   # Allows access to samples
        self.rx_thread = None                                               # Reception thread
        self.rx_continuous_sampling = True                                  # Allows continuous sampling function


        try:
            self._usrp = uhd.usrp.MultiUSRP()
        except Exception:
            print('USRP not connected')
   
    def printConfiguration(self) -> None:
        '''
        Display the current configuration settings of the USRP device.

        This method prints  out various parameters related to the USRP's
        operation, including master clock rate, channel mapping, receive
        and transmit sample rates, center frequencies, gains, and buffer
        lengths.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        
        
        print("--------------------------------------")
        print("          USRP CONFIGURATION          ")
        print("--------------------------------------")
        print("Master clock rate: ", self.master_clock_rate)
        print("Selected Channel: ", self.channel_mapping)
        print("Rx Sample Rate: ", self.rx_sample_rate)
        print("Rx Center Frequency: ", self.rx_center_freq)
        print("Rx Gain: ", self.rx_gain)
        print("Rx Number of Samples: ", self.rx_num_samps)
        print("Rx Buffer Length: ", self.rx_buffer_length,"\n")
        print("Tx Sample Rate: ", self.tx_sample_rate)
        print("Tx Center Frequency: ", self.tx_center_freq)
        print("Tx Gain: ", self.tx_gain)
        print("Tx Buffer Length: ", self.tx_buffer_length)
        print("--------------------------------------")
        

    '''-------------------------------------------------------------------------------------------------------------------------------
                        RECEPTION SECTION
    ----------------------------------------------------------------------------------------------------------------------------------'''
        
    def setReceiver(self):
        '''
        Configure the receiver settings for the USRP device.

        This  method sets the master  clock rate, sample rate, center frequency,
        and gain for the receiver. It also prepares the receive buffer to ensure
        proper data handling during operation.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        
        # Baseband and RF configuration
        self._usrp.set_master_clock_rate(self.master_clock_rate)
        self._usrp.set_rx_rate(self.rx_sample_rate, self.channel_mapping)
        self._usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(self.rx_center_freq), self.channel_mapping)
        self._usrp.set_rx_gain(self.rx_gain, self.channel_mapping)

        self.setReceiveBuffer()

        # # Set up the stream and receive buffer
        # st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        # st_args.channels = [self.channel_mapping]
        # self.metadata = uhd.types.RXMetadata()
        # self.streamer = self._usrp.get_rx_stream(st_args)
        # self.recv_buffer = np.zeros((1, self.buffer_length), dtype=np.complex64)
        
    def setReceiveBuffer(self):
        '''
        Initialize the receive buffer and streaming configuration for the USRP device.

        This method sets  up the necessary  parameters for receiving data, including stream
        arguments and the allocation of a buffer to store incoming samples. It ensures that
        the device is ready to handle incoming data efficiently.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        
        # Set up the stream and receive buffer
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [self.channel_mapping]
        self.rx_metadata = uhd.types.RXMetadata()
        self.rx_streamer = self._usrp.get_rx_stream(st_args)
        self.recv_buffer = np.zeros((1, self.rx_buffer_length), dtype=np.complex64)

    def startRxStream(self):
        '''
        Start the continuous reception stream for the USRP device.

        This method  issues a command  to begin streaming  data from the receiver,
        allowing for real-time data acquisition. It configures the stream to start
        immediately, ensuring that data is captured without delay.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        self.stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        self.stream_cmd.stream_now = True
        self.rx_streamer.issue_stream_cmd(self.stream_cmd)
    
    def stopRxStream(self):
        '''
        Stop the continuous reception stream for the USRP device.

        This method  issues a command to  halt the data streaming from 
        the receiver, effectively stopping real-time data acquisition. 
        It ensures that the receiver is no longer capturing data until 
        restarted.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        self.stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        self.rx_streamer.issue_stream_cmd(self.stream_cmd)

    def getSamples(self):
        '''
        Retrieve a specified number of samples from the USRP receiver.

        This method collects  raw data samples from the receiver in frames,
        storing  them in an array for  further processing. It  ensures that 
        the samples are gathered efficiently based on the configured buffer 
        length and number of samples.

        Args:
            self: The instance of the class.

        Returns:
            rx_samples (numpy.ndarray): An array containing the retrieved samples.
        '''
        # Get 1 frame of raw data
        # self.rx_samples = np.zeros(self.rx_num_samps, dtype=np.complex64) # Already declared in the constructor
        for i in range(self.rx_num_samps//self.rx_buffer_length):
            self.rx_streamer.recv(self.recv_buffer, self.rx_metadata)
            self.rx_samples[i*self.rx_buffer_length:(i+1)*self.rx_buffer_length] = self.recv_buffer[0]  #Save every pow of 2 samples
        return self.rx_samples
    
    # WARNING: ONLY USE IN A DAEMON THREAD!!!
    # Private function, used in 'startRxThread()'
    def _continuousRxSampling(self):
        '''
        Continuously sample data from the USRP receiver while enabled.

        This method enters a loop that repeatedly retrieves samples from 
        the receiver as long as the continuous sampling flag is set to true.
        It ensures ongoing data acquisition for real-time processing.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        while self.rx_continuous_sampling:
            self.getSamples()
    
    def getPower_dBm(self, samples):
        '''
        Calculate the received power in decibels relative to one milliwatt (dBm).

        This method computes the power of the provided samples by summing the 
        squared magnitudes and converting the result to dBm using the power
        formula for voltage signal. It provides a measure of the signal strength.

        Args:
            self: The instance of the class.
            samples (numpy.ndarray): The array of received samples for which to calculate power.

        Returns:
            float: The calculated power in dBm.
        '''
        # Compute the received power in dBm
        return 10*np.log10(1e3*np.sum(np.square(np.abs(samples)))/(2*self.z0*self.rx_num_samps)) # power dBm
    
    def updateRxGain(self, new_gain):
        '''
        Dynamically update the receive gain of the USRP device.

        This method sets a new gain value for the receiver and updates 
        the internal state to reflect this change. It allows for real-time
        adjustments to the gain, which can be crucial for optimizing signal 
        reception.

        Args:
            self: The instance of the class.
            new_gain (float): The new gain value to be set for the receiver.

        Returns:
            None
        '''
        # Used to dynamically change the USRP Rx gain
        self._usrp.set_rx_gain(new_gain, self.channel_mapping)
        self.rx_gain = new_gain
        print("New USRP gain: ", self.rx_gain)

    ''' -------------- RX THREADING FUNCTIONS --------------'''

    def startRxThread(self):
        '''
        Initialize and start the receiver thread for continuous data sampling.

        This method sets up the USRP receiver and begins streaming data to the host. 
        It creates a separate thread to handle continuous sampling, allowing for 
        real-time data acquisition without blocking the main program.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        self.setReceiver()          # USRP rx initialization
        self.startRxStream()        # Start USRP transmission to host
        self.rx_thread = threading.Thread(target=self._continuousRxSampling, name="USRP_RX_THREAD",daemon=True)
        self.rx_thread.start()      # Star thread
    
    def stopRxThread(self):
        '''
        Stop the receiver thread and halt continuous data sampling.

        This method sets the flag to stop continuous sampling, waits for 
        the receiver thread to finish, and stops the data transmission 
        from the USRP to the host. It ensures that all resources are 
        properly released before concluding the data acquisition process.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        self.rx_continuous_sampling = False     # Stop _continuousRxSampling
        self.rx_thread.join()                   # Waits to USRP_RX_THREAD to finish
        self.stopRxStream()                     # Stop USRP transmission to host

    '''-------------------------------------------------------------------------------------------------------------------------------
                        TRANSMISSION SECTION
    ----------------------------------------------------------------------------------------------------------------------------------'''

    def transmission(self, duration):
        '''
        Transmit a waveform signal using the USRP device.

        This method generates a sinusoidal waveform based on the configured transmission 
        frequency and sends it through the USRP for a specified duration. It allows for 
        the transmission of signals for testing or communication purposes.

        Args:
            self: The instance of the class.
            duration (float): The duration for which the waveform should be transmitted, in seconds.

        Returns:
            None
        '''
        t = np.linspace(0,1/self.tx_center_freq,2000)
        tx_samples = 0.1*np.sin(2*np.pi*self.tx_center_freq*t)
        
        self._usrp.send_waveform(tx_samples, duration, self.center_freq, self.sample_rate, self.channel_mapping, self.tx_gain)

    def setTransmitter(self):
        '''
        Configure the transmitter settings for the USRP device.

        This  method  sets  the necessary  parameters for the transmitter, 
        including  the  master clock  rate, sample rate, center frequency, 
        and gain. It prepares the USRP for transmitting signals effectively.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        # Baseband and RF configuration
        self._usrp.set_master_clock_rate(self.master_clock_rate)
        self._usrp.set_tx_rate(self.tx_sample_rate, self.channel_mapping)
        self._usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(self.tx_center_freq), self.channel_mapping)
        self._usrp.set_tx_gain(self.tx_gain, self.channel_mapping)

        self.setTransmitterStreamer()

    def setTransmitterStreamer(self):
        '''
        Initialize the transmitter streamer configuration for the USRP device.

        This method sets up the streaming parameters for transmitting data, including the format and 
        channel mapping. It prepares the USRP to handle outgoing signals effectively.

        Args:
            self: The instance of the class.

        Returns:
            None
        '''
        # Streamer configuration
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [self.channel_mapping]
        self.tx_metadata = uhd.types.TXMetadata()
        self.tx_streamer = self._usrp.get_tx_stream(st_args)
    
    def sendSignal(self, signal: np.array, tx_duration):
        '''
        Transmit a given signal using the USRP device for a specified duration.

        This method sends the provided signal in chunks to the USRP for transmission, ensuring that the 
        total number of samples sent corresponds to the desired duration. It handles the transmission 
        process and signals the end of the burst once completed.

        Args:
            self: The instance of the class.
            signal (np.array): The signal to be transmitted, represented as a NumPy array.
            tx_duration (float): The duration for which the signal should be transmitted, in seconds.

        Returns:
            None
        '''
        total_tx_samples = int(np.floor(tx_duration * self.tx_sample_rate))
        sent_samples = 0
        signal_length = signal.size
        while sent_samples < total_tx_samples:
            pending_samples = min(signal_length, total_tx_samples-sent_samples)
            if pending_samples < signal_length:
                sum_samples = self.tx_streamer.send(signal[:pending_samples]) # Samples just sent by USRP
            else:
                sum_samples = self.tx_streamer.send(signal, self.tx_metadata)
            sent_samples += sum_samples

        # Send EOB to terminate TX
        self.tx_metadata.end_of_burst = True
        self.tx_streamer.send(np.zeros((1,1), dtype=np.complex64), self.tx_metadata)

        self.tx_streamer = None
        
# End of the class USRP

'''
To do: 
        - Add function to check and configure multiple channels (usually max 2).
        - All configuration parameters should be an array of length equal to number of channels
        - Add function to correct measures in real time.
'''

'''------------------------------------------------------------------------------------------'''

def spectrum(usrp_test:USRP, tx = False, signal = np.ones(10)):
        frequency = np.fft.fftshift(np.fft.fftfreq(usrp_test.rx_num_samps,d=1/usrp_test.rx_sample_rate)) + usrp_test.rx_center_freq
        window = np.hamming(usrp_test.rx_num_samps)
        spec = np.zeros(usrp_test.rx_num_samps)
        fig_,ax = plt.subplots(1,1)
        ln, = ax.plot([],[])
        ann1 = ax.annotate(
                    "Power: ",
                    (0, 1),
                    xycoords="axes fraction",
                    xytext=(10, -10),
                    textcoords="offset points",
                    ha="left",
                    va="top",
                    animated=True,
                )
            
        def init():
            ax.grid("on")
            ax.set_xlabel("Frequency [MHz]")
            ax.set_ylabel("Magnitude [dB]")
            ax.set_ylim(-50, 10)
            ax.set_xlim(usrp_test.rx_center_freq-usrp_test.rx_sample_rate/2,usrp_test.rx_center_freq+usrp_test.rx_sample_rate/2)
            return (ln, ann1)
        
        def update_power(frame, spec):
            try:
                s = usrp_test.getSamples()
                sw = np.multiply(window,s[0])
                if len(s) == usrp_test.rx_num_samps:
                    spec = np.square(np.abs(np.fft.fftshift(np.fft.fft(sw))))
                    spec = 10*np.log10(spec)
                
                ln.set_data(frequency, spec)
                pow_samples = usrp_test.getPower_dBm(s)
                ann1.set_text(f"Power from samples: {pow_samples: .4f} dBm")
            except Exception as e:
                print(e)

            return (ln, ann1)
        
        print("Configure USRP")
        #usrp_test = USRP(name = "USRP B200 mini", freq=freq, 
        #                 rx_rate=5e6, rx_samples = rx_samples, rx_gain=0, 
        #                 tx_gain=90, 
        #                 calibration_file="AF_B200_mini")
        # usrp_test = USRP(name = "USRP B200 mini", freq=5.8e9, 
        #                  rx_rate=5e6, rx_samples = rx_samples, rx_gain=0, 
        #                  tx_gain=0, 
        #                  calibration_file="AF_B200_mini_5_8GH")
        print("Finish the configuration")
        
        # usrp_test.check_channels()
        # usrp_test.set_received_stream()        
        # rx_thread = threading.Thread(target=usrp_test.rx_thread, daemon= True)
        # rx_thread.start()

        usrp_test.startRxThread()

        # if tx:
        #     usrp_test.set_transmitter_stream(signal= signal)
        #     tx_thread = threading.Thread(target=usrp_test.tx_thread, daemon= True)
        #     tx_thread.start()
        anim = animation.FuncAnimation(fig=fig_, init_func=init, func=update_power, fargs = (spec,),
                                       frames = 1000, interval = 20, blit=True)
        plt.show()
        # if tx:
        #     tx_thread.join()
        
        # usrp_test._stream = False
        # rx_thread.join()
        usrp_test.stopRxThread()

if __name__ == "__main__":
    try:
        usrp_UT = USRP(rx_gain=20)
        spectrum(usrp_UT)
    except KeyboardInterrupt:
        print("Process Interrupted")
        usrp_UT.stopRxThread()




## [⬅️](../README.md)

<!--
https://tutorialmarkdown.com/emojis
-->

# Driver UHD and GNURadio software installation

This file provides instructions for installing the UHD (USRP Hardware Driver) and GNURadio software on a Windows x64 system. It includes links to the necessary drivers and packages from Ettus Research, as well as steps for setting up the environment variables required for the installation. This document is intended to guide users through the process of configuring their system to work with UHD and GNURadio on a Windows OS.

## For Windows x64

Links UHD-USRP:

- [Ettus UHD](https://files.ettus.com/binaries/uhd_stable/uhd_004.006.000.000-release/4.6.0.0/Windows-10-x64/)

- Ettus USRP [Driver (Windows)](https://files.ettus.com/manual/page_transport.html#transport_usb_installwin)

Set Drivers:

|*On User variables > Path:*|Add path of package UHD|
|-|-|
|Variable name:| `Path`|
|Variable value:| `C:\Program Files\UHD`|

|*On System variables:*|Create path of Driver USRP|
|-|-|
|Variable name:| `UHD_IMAGES_DIR`|
|Variable value:| `C:\Program Files\UHD\share\uhd\images`|

<br>

![Example set path](/Docs/imgs/image_path.png)

- Copy the file "libusb-1.0.dll" to the path
```C:\Windows\System32```

- Test the installation in CMD with USRP connected:

    ```
    >> uhd_find_devices
    ```

    ![UHD find devices](/Docs/imgs/cmd_uhd_find_devices.png)

<br>

# Using GNU Radio:<br>

Download directly GNURadio [Radioconda](https://wiki.gnuradio.org/index.php/InstallingGR) (Recomended) and install  package <i>radioconda.exe</i>

## Installing packages whit conda using terminal

*(Run CMD or PowerShell as administrator)* <br>

Example: adding packages for use <i>uhd package</i> on <i> Jupiter Noteboook </i> for VS Code:

```
>> cd C:\ProgramData\radioconda\Scripts
>> conda.exe install ipykernel --update-deps
```

- Modifying conda executables for convenience:<br>
*(Only if we have other versions of python already installed)*

    |Change| To|
    |-|-|
    |`C:\ProgramData\radioconda\Scripts\conda.exe`|`C:\ProgramData\radioconda\Scripts\radioconda.exe`|
    |`C:\ProgramData\radioconda\Scripts\conda-script.py`|`C:\ProgramData\radioconda\Scripts\radioconda-script.py`|
    and <i>Add Environment variable</i> `C:\ProgramData\radioconda\Scripts`

<!-- ## Linux Ubuntu 22 -->
Documentation PySDR -API:

- [PySDR: A Guide to SDR and DSP using Python](https://pysdr.org/content/usrp.html)

# Example: Using UHD python API [🔝](#driver-uhd-and-gnuradio-software-installation)

Example test for Rx:

```python
import uhd
import numpy as np

usrp = uhd.usrp.MultiUSRP()

# Model: B200
# serial number: 31BA1B2

num_samps = 10000 # number of samples received
center_freq = 100e6 # Hz
sample_rate = 1e6 # Hz
gain = 50 # dB

usrp.set_rx_rate(sample_rate, 0)
usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), 0)
usrp.set_rx_gain(gain, 0)

# Set up the stream and receive buffer
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = [0]
metadata = uhd.types.RXMetadata()
streamer = usrp.get_rx_stream(st_args)
recv_buffer = np.zeros((1, 1000), dtype=np.complex64)

# Start Stream
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
stream_cmd.stream_now = True
streamer.issue_stream_cmd(stream_cmd)

# Receive Samples
samples = np.zeros(num_samps, dtype=np.complex64)
for i in range(num_samps//1000):
    streamer.recv(recv_buffer, metadata)
    samples[i*1000:(i+1)*1000] = recv_buffer[0]

# Stop Stream
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
streamer.issue_stream_cmd(stream_cmd)

print(len(samples))
print(samples[0:10])
```

## UHD error [🔝](#driver-uhd-and-gnuradio-software-installation)

- [UHD utility function rx_samples_to_file incorrectly errors out for "RX channel out of range"](https://github.com/EttusResearch/uhd/issues/723)

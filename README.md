# MP3 to strobe lights algorithm

:rotating_light: **WARNING: THIS ALGORITHM PRODUCES RAPIDLY FLASHING LIGHTS.** :rotating_light:

Algorithm to generate a strobe light effect by alternating white and black fullscreen using PySimpleGUI. This is a *math-heavy* project.

## How to use
1. place a MP3 file in the same directory as main.py
2. change the FILE_NAME variable on line 17 of main.py
3. (OPTIONAL) Other variables such as the volume can be changed at lines 16-21 in main.py
   - VOLUME variable should be kept low (try to start at 5-10)

## More about the algorithm
This algorithm works like a beat detection algorithm, which uses FFT's (Fast Fourier Transform) and statistical analysis to detect spikes at certain frequencies. The SENSIBILITY_CONST variable used in the algorithm changes the sensibility to changes as the name suggests.

The *sound energy* of each subband is evaluated over time and compared to the average *sound energy* of an interval of time around the current time. A spike is detected when the current time's *sound energy* is higher than average.

More information about the algorithm can be found [here](https://archive.gamedev.net/archive/reference/programming/features/beatdetection/index.html).

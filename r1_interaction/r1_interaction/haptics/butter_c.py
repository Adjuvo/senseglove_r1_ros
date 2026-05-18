""" 
Basic Butterworth filtering script
"""

from scipy import signal
import numpy as np

class Butter_C:

    def __init__(self, ftype, cutoff, fs, n_dimensions=1, order=2) -> None:
        self.fs = fs
        self.n_dimensions = n_dimensions
        self.sos = signal.butter(order, cutoff, ftype, fs=fs, output='sos')
        self.init_filter(n_dimensions)        
        
    def init_filter(self, n_dimensions):
        self.zi = signal.sosfilt_zi(self.sos)
        # self.zi = np.repeat(np.expand_dims(self.zi, axis=2), n_dimensions, axis=2)
        self.first_step = True

    def filter(self, raw, axis=0):
        # if self.first_step:
        #     self.first_step = False
        #     self.zi *= raw
        filtered, self.zi = signal.sosfilt(self.sos, raw, zi=self.zi, axis=axis)
        
        return filtered.reshape((-1))
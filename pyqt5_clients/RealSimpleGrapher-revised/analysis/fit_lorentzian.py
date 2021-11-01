# Fitter class for Lorentzians

from .model import Model, ParameterInfo
import numpy as np

class Lorentzian(Model):

    def __init__(self):
        self.parameters = {
            'center': ParameterInfo('center', 0, self.guess_center),
            'scale': ParameterInfo('scale', 1, self.guess_scale),
            'fwhm': ParameterInfo('fwhm', 2, self.guess_fwhm),
            'offset': ParameterInfo('offset', 3, self.guess_offset)
            }

    def model(self, x, p):
        '''
        Base Lorentzian model. Using definition from
        http://mathworld.wolfram.com/LorentzianFunction.html

        where we add an overall scale factor to change the
        peak height

        p = [center, scale, gamma, offset]
        '''
        p[2] = abs(p[2]) # fwhm is positive
        return p[3] +  p[1]*0.5*p[2]/( (x - p[0])**2 + (0.5*p[2])**2)

    def guess_center(self, x, y):
        #Fred: make it negative for better fitting as our spectrum is absorption
        #max_index = np.argmax(y)
        min_index = np.argmin(y)
        return x[min_index]

    def guess_scale(self, x, y):
        area = (max(x) - min(x))*(max(y) - min(y))
        #Fred: make it negative for better fitting as our spectrum is absorption
        return -area
    
    def guess_fwhm(self, x, y):
        return (max(x) - min(x))/6.0
    
    def guess_offset(self, x, y):
        return np.min(y)

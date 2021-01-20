# Fitter class for linear fits

from .model import Model, ParameterInfo
import numpy as np

class CosFit(Model):
    def __init__(self):
        self.parameters = {
            'A':ParameterInfo('A', 0, self.guess_a),
            'T':ParameterInfo('T', 1, self.guess_t),
            'Theta':ParameterInfo('Theta', 2, self.guess_theta),
            'O':ParameterInfo('O', 3, self.guess_o),
        }
        self.guessedA = None

    def model(self, x, p):
        A = p[0]
        T = p[1]
        Theta = p[2]
        O = p[3]
        return A*np.cos(2*np.pi*T*x + Theta) + O

    def guess_placeholder(self, x, y):
        if self.guessedA is not None:
            return
        x, y = list(zip(*sorted(zip(x, y))))
        x = np.array(x)
        y = np.array(y)
        maximum = np.amax(y)
        minimum = np.amin(y)
        self.guessedA = (maximum-minimum)/2
        self.guessedO = (maximum-minimum)/2
        maxindex = np.argmax(y)
        self.guessedTheta = x[maxindex]

        threshold = (maximum+minimum)/2.0
        NewZeroCrossing = x[0]
        PreviousZeroCrossing = x[0]
        maxZeroCrossingDelta = 0
        for ind in range(len(y)-1):
            if (y[ind] <= threshold <= y[ind+1]) or (y[ind+1] <= threshold <= y[ind]):
                NewZeroCrossing = x[ind]
                NewZeroCrossingDelta = NewZeroCrossing-PreviousZeroCrossing
                if NewZeroCrossingDelta > maxZeroCrossingDelta:
                    maxZeroCrossingDelta = NewZeroCrossingDelta 
                PreviousZeroCrossing = NewZeroCrossing
        self.guessedT = 1.0/(2.0*maxZeroCrossingDelta)

    def guess_a(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedA

    def guess_t(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedT

    def guess_theta(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedTheta

    def guess_o(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedO

class SinCosFit(Model):
    def __init__(self):
        self.parameters = {
            'A': ParameterInfo('A', 0, self.guess_a),
            'B': ParameterInfo('B', 1, self.guess_b),
            'k': ParameterInfo('k', 2, self.guess_k),
            'O': ParameterInfo('O', 3, self.guess_o),
        }
        self.guessedA = None

    def model(self, x, p):
        A = p[0]
        B = p[1]
        k = p[2]
        O = p[3]
        return A*np.sin(2*np.pi*k*x) + B*np.cos(2*np.pi*k*x) + O

    def guess_placeholder(self, x, y):
        if self.guessedA is not None:
            return
        x,y = zip(*sorted(zip(x, y)))
        x = np.array(x)
        y = np.array(y)
        maximum = np.amax(y)
        minimum = np.amin(y)
        self.guessedA = (maximum-minimum)/2
        self.guessedO = (maximum+minimum)/2
        maxindex = np.argmax(y)
        self.guessedB = 0;
        threshold = (maximum+minimum)/2.0
        NewZeroCrossing = x[0]
        PreviousZeroCrossing = x[0]
        maxZeroCrossingDelta = 0
        for ind in range(len(y)-1):
            if (y[ind] <= threshold <= y[ind+1]) or (y[ind+1] <= threshold <= y[ind]):
                NewZeroCrossing = x[ind]
                NewZeroCrossingDelta = NewZeroCrossing-PreviousZeroCrossing
                if NewZeroCrossingDelta > maxZeroCrossingDelta:
                    maxZeroCrossingDelta = NewZeroCrossingDelta
                PreviousZeroCrossing = NewZeroCrossing
        self.guessedK = 1.0/(2.0*maxZeroCrossingDelta)

    def guess_a(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedA

    def guess_b(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedB

    def guess_k(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedK

    def guess_o(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedO

# Still problematic. Use Cos Instead
class CosSqFit(Model):
    def __init__(self):
        self.parameters = {
            'A':ParameterInfo('A', 0, self.guess_a),
            'T':ParameterInfo('T', 1, self.guess_t),
            'Theta':ParameterInfo('Theta', 2, self.guess_theta),
            'O':ParameterInfo('O', 3, self.guess_o),
        }
        self.guessedA = None

    def model(self, x, p):
        A = p[0]
        T = p[1]
        theta = p[2]
        O = p[3]
        return A*np.square(np.cos(np.pi/2/T*x+theta))+O

    def guess_placeholder(self, x, y):
        if self.guessedA is not None:
            return
        x, y = list(zip(*sorted(zip(x, y))))
        x = np.array(x)
        y = np.array(y)
        maximum = np.amax(y)
        minimum = np.amin(y)
        self.guessedA = (maximum-minimum)/2
        self.guessedO = (maximum-minimum)/2
        maxindex = np.argmax(y)
        self.guessedTheta = x[maxindex]

        threshold = (maximum+minimum)/2.0
        NewZeroCrossing = x[0]
        PreviousZeroCrossing = x[0]
        maxZeroCrossingDelta = 0
        for ind in range(len(y)-1):
            if (y[ind] <= threshold <= y[ind+1]) or (y[ind+1] <= threshold <= y[ind]):
                NewZeroCrossing = x[ind]
                NewZeroCrossingDelta = NewZeroCrossing-PreviousZeroCrossing
                if NewZeroCrossingDelta > maxZeroCrossingDelta:
                    maxZeroCrossingDelta = NewZeroCrossingDelta 
                PreviousZeroCrossing = NewZeroCrossing
        self.guessedT = 1.0/(2.0*maxZeroCrossingDelta)

    def guess_a(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedA

    def guess_t(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedT

    def guess_theta(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedTheta

    def guess_o(self, x, y):
        self.guess_placeholder(x, y)
        return self.guessedO


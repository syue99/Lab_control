'''
Configuration settings for Grapher gui 
  
'''

import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

GLOBALCOLORS = ["#000000", "#3b3353", "#f27c85", "#006477", "#ad5262", "#cc6c5c"]
GLOBALFITCOLORS = ["#000000", "#3b3353", "#f27c85", "#006477", "#ad5262", "#cc6c5c"]
HistOpacity = 'B2'
FitLineWidth = 2

class traceListConfig():
    def __init__(self, background_color = 'white', use_trace_color = True):
        self.background_color = background_color
        self.use_trace_color = use_trace_color


import labrad
import tables as tb
import numpy as np
cxn = labrad.connect() ## connect to labrad server

Z1 = np.random.random((50,50)) ## generate random images
Z2 = np.random.random((50,50)) 

## relevant functions are inside datavauilt class, especially after line 1386
#save_image(self, c, data, image_size, repetitions, filename,imagedir='/', filetype='.npy')
#open_image(self, c, filename, imagename, imagedir='/',rowrange=[None,None], filetype='.h5')
#stream_h5image(self, c,filename, limit=None, startOver=True, rowrange=[None,None])

cxn.data_vault_tables.save_image(Z1,2500,1,"test-h51",filetype='.h5')


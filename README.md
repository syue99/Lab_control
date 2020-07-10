# Lab_control
This repo is the code for the lab control system of the lab. We use Labrad (https://sourceforge.net/p/labrad/wiki/Home/) as the base of our system. We also credit to Prof. Haffner (https://github.com/HaeffnerLab/Haeffner-Lab-LabRAD-Tools ; https://github.com/AMOLabRAD/AMOLabRAD/wiki) and Prof. Jayich (private repo for their pydux module) for the help. For any question, please contact ys3135@nyu.edu. The master branch is the labarad that is still under development and the ver0.0 branch is the first running ver. of labrad with pulser, pmt, realsimple grapher, and fitting modules. Please refer to the group presentation slides (07/07/20) in group wiki for more details. (Note that in vers. 0.0 there is more detailed instructions for setting up the enviroment in the documentation page, while in the master branch we will include new feartures in the documenation.


## Data-Vault
Data-Vault server is responsible for storing the experiment data and provides a convenient way to add/modify datasets in the labrad environment. 
To run the data-vault server, execute PATH-TO\pydux-master\lib\control\servers\data_vault\data_vault.py
Basic operations like creating dataset, adding data points, and editing existing datasets is shown in the snippet below
```python
import labrad
cxn = labrad.connect()
cxn.data_vault.new('Half-Life', [('x', 'in')], [('y','','in')]) ## creates a new,empty dataset called 'Half-Life-0000n' with independent variable x and dependent variable y. 
cxn.data_vault.add([[1,3],[2,4]]) ## add data points
cxn.data_vault.open_appendable("00001 - Half-Life") ## open file in append mode
cxn.data_vault.variables() ## list of variables with their units in the form of [(xVariableName,'unit'),('yVariableName','unit')]
```
There is also the option of specifying parameters, units, among other features. 

## Live Graphing
Real-time graphing of data in labrad is achieved using the RealSimpleGrapher. A working copy of all the associated modules can be found in RealSimpleGrapher-backup folder. 
To launch the GUI application, run RealSimpleGrapher-backup/rsg.py
RealSimpleGrapher has live plotting, rescaling, downsampling, and fitting capabilities. 
To add a dataset, right click on the left pane of the rsg window, and select 'Add Data Set'.
To fit a curve to the dataset, right click on the dataset name in rsg, select 'Fit'. We have the option to choose from Lorenzian, Gaussian, Bessel, Linear and Rabi function fitting. 

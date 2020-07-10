# Installation

## Windows OS
In this section, we will talk about how to install the required environment of the vers.0.0 labrad on a Windows 10 computer.
Let's assume you start with an empty computer. The following steps take credits from Prof. Jayich's group at UCSB.

### Step1: Initial set-up
For installing Windows, you can get an installation disc from the PCS, or use [Windows install media tool](https://www.microsoft.com/en-us/software-download/windows10) to create a USB windows install drive (Select Windows 10 Pro or Windows 10 Education for 64 bit). Talk with Raj to get buy a key or talk with Fred to get a spare key. 

You can name the PC labuser with password funinthelab. This is our default set up. 

Disable sleep or hibernate on the computer if it will be used to control instruments. Allow remote desktop into the computer. Also consider [disabling the windows update using the group policy editer](https://www.easeus.com/todo-backup-resource/how-to-stop-windows-10-from-automatically-update.html#part2) because it causes unexpected restarts (even during experiments!).

Download and install Google Chrome, 7-zip, and your favorite text editor.

### Step2: get Code and Git repos

Under the labuser folder (Usually in `C:\Users\labuser`), create a folder called `code`.

Download Github Desktop, log into our github group, in configure Git page enter your Github username and email, and you should be able to clone the following repositories to the local computer in the `code` folder just created:
- control system (https://github.com/PreciselyQuantum/Lab_control) (Note you need to switch to ver-0.0 branch to get stable initial version code)

### Step3: Install Python and related packages
* Download **Anaconda3**, and install it. During the install, **make sure that the option to Add Anaconda to my PATH environment variable is checked**, and it is installed in the user folder (`C:\Users\scientist\Anaconda3`).
* Download [Build Tools for Visual Studio 2017](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2017), and install it with only all components in Visual C++ (including the Windows SDK).
* After installation, create a new **python 3.6** environment in Anaconda3 called "code3". This can be done in Anaconda Navigator or via command line. [tutorial](https://conda.io/docs/user-guide/tasks/manage-environments.html) for details. Or you can type `conda create -n code3 python=3.6` in anaconda prompt
* Open cmd and run `activate code3`.
* Run `pip install pylabrad spinmob pycodestyle nose pyqt5 pyqtgraph pywin32 ok ipython matplotlib scipy numpy qt5reactor jupyter treedict==0.2.2 pyserial pyvisa sympy mcculw coverage Cython statsmodels pillow`.
* Run `pip install qutip`.
* You will need to change directory to `C:\Users\labuser\Anaconda3\envs\code3\Lib\site-packages\ok` and change all the files there with all files in ok_backup from the environment branch (will set up later) or back_up packages in the lab NAS system.
* You will also need to install pyqt4 related packages if you want to run any file in the pyqt4-client. You will need to get a pyqt4 wheel file from the environment branch/backup. You will need to `pip install /directory/to/whl/file` and continue if there isn't any error messege. You will also need to run `pip install qt4reactor` and then change the file there with all files in qt4reactor from the environment branch/backup.


### Step4: Finalize and run LabRAD Manager

Install [Java](https://www.java.com/en/download/) if not already installed. Current version of 2018/11/10 is Java 8 update 191. JDK (Java Development Kit) is not needed if you wonder about it.

Install [Chromium] blue chrome
Install the Chromium from the environment branch/set-up. This is a version of old chrome that support the front-end of labrad (scalabrad_web) of current version(2.0.6). Normal browser can be used if the new version fix the compatability issue.

Run labrad manager and front-end by running the scalabrad.bat and scalabradweb.bat from the corresponding folders (in this repo). If there isn't any error message, open the chromium and try to access `localhost:7667`. Otherwise, look for the error message, which possibly is due to a wrong directory address leading to an non-exisiting Java folder. Try to fix the issue by reset the address in the bat file.

Run datavault.py, paravault.py, pulser.py.. by opening a new anaconda prompt and activate to code3 enviroment by running `conda activate code3` first and then `python \directory\to\file`. You should be good to go. Note that you might need to change configuration file in the config folder for pulser if you are connecting a new fpga.


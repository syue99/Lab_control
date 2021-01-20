from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks, returnValue
from connection import connection
from DDS_CONTROL import DDS_CHAN, DDS_MOVING_LATTICE_CHAN

'''
The Switch Control GUI lets the user control the TTL channels of the Pulser

Version 1.0
'''

SWITCHSIGNALID = 378902
DDSSIGNALID = 319182

class combinedWidget(QtGui.QFrame):
	def __init__(self, reactor, cxn = None, parent=None):
		super(combinedWidget, self).__init__(parent)
		self.initialized = False
		self.reactor = reactor
		self.cxn = cxn
		self.connect()

	@inlineCallbacks
	def connect(self):
		if self.cxn is  None:
			self.cxn = connection()
			yield self.cxn.connect()
			from labrad.types import Error
			self.Error = Error
		self.context = yield self.cxn.context()
		try:
			displayed_channels = yield self.switches_get_displayed_channels()
			# newly added
			self.display_channels, self.widgets_per_row = yield self.dds_get_displayed_channels()
			self.widgets = {}.fromkeys(self.display_channels)
			yield self.initializeGUI(displayed_channels)
			yield self.setupListeners()
		except Exception as e:
			print (e)
			print ('SWTICH CONTROL: Pulser not available')
			self.setDisabled(True)
		self.cxn.add_on_connect('Pulser', self.reinitialize)
		self.cxn.add_on_disconnect('Pulser', self.disable)

	@inlineCallbacks
	def switches_get_displayed_channels(self):
		'''
		get a list of all available channels from the pulser. only show the ones
		listed in the registry. If there is no listing, will display all channels.
		'''
		server = yield self.cxn.get_server('Pulser')
		all_channels = yield server.get_channels(context = self.context)
		all_names = [el[0] for el in all_channels]
		channels_to_display = yield self.switches_registry_load_displayed(all_names)
		if channels_to_display is None:
			channels_to_display = all_names
		channels = [name for name in channels_to_display if name in all_names]
		returnValue(channels)


	# newly added
	@inlineCallbacks
	def dds_get_displayed_channels(self):
		'''
		get a list of all available channels from the pulser. only show the ones
		listed in the registry. If there is no listing, will display all channels.
		'''
		server = yield self.cxn.get_server('Pulser')
		all_channels = yield server.get_dds_channels(context = self.context)
		#print (all_channels)
		channels_to_display, widgets_per_row = yield self.dds_registry_load_displayed(all_channels, 1)
		if channels_to_display is None:
			channels_to_display = all_channels
		if widgets_per_row is None:
			widgets_per_row = 1
		channels = [name for name in channels_to_display if name in all_channels]
		returnValue((channels, widgets_per_row))

	@inlineCallbacks
	def dds_registry_load_displayed(self, all_names, default_widgets_per_row):
		reg = yield self.cxn.get_server('Registry')
		yield reg.cd(['Clients','DDS Control'], True, context = self.context)
		try:
			displayed = yield reg.get('display_channels', context = self.context)
		except self.Error as e:
		#There is a catch here, as we used python 3 and newer vers. of labrad, the e returned is no longer 21
		#So we changed the code here from ==21 to !=21, but then if we have other problem we cannot raise exception any more
			if e.code != 21:
				#key error
				yield reg.set('display_channels', all_names, context = self.context)
				displayed = None
			else:
				raise
		try:
			widgets_per_row = yield reg.get('widgets_per_row', context = self.context)
		except self.Error as e:
			if e.code != 21:
				#key error
				yield reg.set('widgets_per_row', 1, context = self.context)
				widgets_per_row = None
			else:
				raise
		returnValue((displayed, widgets_per_row))

	@inlineCallbacks
	def switches_registry_load_displayed(self, all_names):
		reg = yield self.cxn.get_server('Registry')
		yield reg.cd(['Clients','Switch Control'], True, context = self.context)
		try:
			displayed = yield reg.get('display_channels', context = self.context)
		except self.Error as e:
			if e.code == 21:
				#key error
				yield reg.set('display_channels', all_names, context = self.context)
				displayed = None
			else:
				raise
		returnValue(displayed)
	
	@inlineCallbacks
	def reinitialize(self):
		self.setDisabled(False)
		server = yield self.cxn.get_server('Pulser')
		if self.initialized:
			yield server.signal__switch_toggled(SWITCHSIGNALID, context = self.context)
			yield server.signal__switch_toggled(DDSSIGNALID, context = self.context)
			for name in self.d.keys():
				self.setStateNoSignals(name, server)
			for widget in self.widgets.values():
				if widget is not None:
					yield widget.setupWidget(connect = False)
		else:
			yield self.initializeGUI()
			yield self.setupListeners()
	
	@inlineCallbacks
	def initializeGUI(self, channels):
		'''
		Lays out the GUI
		
		@var channels: a list of channels to be displayed.
		'''
		server = yield self.cxn.get_server('Pulser')
		self.d = {}
		# set layout
		mainlayout = QtGui.QVBoxLayout()

		# start to init layout for Switches
		switchLayout1 = QtGui.QGridLayout()
		switchLayout2 = QtGui.QGridLayout()
		self.setFrameStyle(QtGui.QFrame.Panel  | QtGui.QFrame.Sunken)
		self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
		# get switch names and add them to the layout, and connect their function
		switchLayout1.addWidget(QtGui.QLabel('Switches'),0,0)
		switchLayout2.addWidget(QtGui.QLabel('Switches'),0,0)
		counter = 0
		for order,name in enumerate(channels):
			# setting up physical container
			groupBox = QtGui.QGroupBox(name) 
			groupBoxLayout = QtGui.QVBoxLayout()
			buttonOn = QtGui.QPushButton('ON')
			buttonOn.setAutoExclusive(True)
			buttonOn.setCheckable(True)
			buttonOff = QtGui.QPushButton('OFF')
			buttonOff.setCheckable(True)
			buttonOff.setAutoExclusive(True)
			buttonAuto = QtGui.QPushButton('Auto')
			buttonAuto.setCheckable(True)
			buttonAuto.setAutoExclusive(True)
			groupBoxLayout.addWidget(buttonOn)
			groupBoxLayout.addWidget(buttonOff)
			groupBoxLayout.addWidget(buttonAuto)
			groupBox.setLayout(groupBoxLayout)
			#adding to dictionary for signal following
			self.d[name] = {}
			self.d[name]['ON'] = buttonOn
			self.d[name]['OFF'] = buttonOff
			self.d[name]['AUTO'] = buttonAuto
			#setting initial state
			yield self.setStateNoSignals(name, server)				   
			buttonOn.clicked.connect(self.buttonConnectionManualOn(name, server))
			buttonOff.clicked.connect(self.buttonConnectionManualOff(name, server))
			buttonAuto.clicked.connect(self.buttonConnectionAuto(name, server))
			counter += 1
			if counter < len(channels) // 2:
				switchLayout1.addWidget(groupBox,0,1 + order)
			else:
				switchLayout2.addWidget(groupBox,0,1 + order%(len(channels)//2))

		mainlayout.addLayout(switchLayout1)
		mainlayout.addLayout(switchLayout2)

		# newly added start to init gui for DDS
		ddsLayout = QtGui.QGridLayout()
		item = 0
		for chan in self.display_channels:
			if chan == "Moving Lattice":
				widget = DDS_MOVING_LATTICE_CHAN(chan, self.reactor, self.cxn, self.context)
				self.widgets[chan] = widget
				ddsLayout.addWidget(widget, item // self.widgets_per_row, item % self.widgets_per_row)
				item += 1
			else:
				widget = DDS_CHAN(chan, self.reactor, self.cxn, self.context)
				self.widgets[chan] = widget
				ddsLayout.addWidget(widget, item // self.widgets_per_row, item % self.widgets_per_row)
				item += 1 

		mainlayout.addLayout(ddsLayout)

		self.setLayout(mainlayout)
		self.initialized = True
	
	@inlineCallbacks
	def setStateNoSignals(self, name, server):
		initstate = yield server.get_state(name, context = self.context)
		ismanual = initstate[0]
		manstate = initstate[1]
		if not ismanual:
			self.d[name]['AUTO'].blockSignals(True)
			self.d[name]['AUTO'].setChecked(True)
			self.d[name]['AUTO'].blockSignals(False)
		else:
			if manstate:
				self.d[name]['ON'].blockSignals(True)
				self.d[name]['ON'].setChecked(True)
				self.d[name]['ON'].blockSignals(False)
			else:
				self.d[name]['OFF'].blockSignals(True)
				self.d[name]['OFF'].setChecked(True)
				self.d[name]['OFF'].blockSignals(False)
	
	def buttonConnectionManualOn(self, name, server):
		@inlineCallbacks
		def func(state):
			yield server.switch_manual(name, True, context = self.context)
		return func
	
	def buttonConnectionManualOff(self, name, server):
		@inlineCallbacks
		def func(state):
			yield server.switch_manual(name, False, context = self.context)
		return func
	
	def buttonConnectionAuto(self, name, server):
		@inlineCallbacks
		def func(state):
			yield server.switch_auto(name, context = self.context)
		return func
	
	@inlineCallbacks
	def setupListeners(self):
		server = yield self.cxn.get_server('Pulser')
		yield server.signal__switch_toggled(SWITCHSIGNALID, context = self.context)
		yield server.addListener(listener = self.followSignalSwitches, source = None, ID = SWITCHSIGNALID, context = self.context)
	   	# newly add
		yield server.addListener(listener = self.followSignalDDS, source = None, ID = DDSSIGNALID, context = self.context)
	
	#Revised by Fred to make it work 
	def followSignalSwitches(self, x, message):
		switchName = message[0]
		state = message[1]
		if switchName not in self.d.keys(): return None
		if state == 'Auto':
			button = self.d[switchName]['AUTO']
		elif state == 'ManualOn':
			button = self.d[switchName]['ON']
		elif state == 'ManualOff':
			button = self.d[switchName]['OFF']
		button.setChecked(True)

	# newly add
	def followSignalDDS(self, x, y):
		chan, param, val = y
		if chan in self.widgets.keys():
			#this check is neeed in case signal comes in about a channel that is not displayed
			print(chan, param, val)
			self.widgets[chan].setParamNoSignal(param, val)

	def closeEvent(self, x):
		self.reactor.stop()
	
	@inlineCallbacks
	def disable(self):
		self.setDisabled(True)
		yield None
			
if __name__=="__main__":
	a = QtGui.QApplication( [] )
	import qt4reactor
	qt4reactor.install()
	from twisted.internet import reactor
	triggerWidget = combinedWidget(reactor)
	triggerWidget.show()
	#a.exec_()
	reactor.run()
"""
### BEGIN NODE INFO
[info]
name = Pulser Shutter Server
version = 1.0
description =
instancename = pulser_shutter_server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

import labrad
from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
try:
    from config.pulser_shutter_server_config import PulserShutterServerConfig
except BaseException:
    from pydux.lib.config.pulser_shutter_server_config import PulserShutterServerConfig


class PulserShutterServer(LabradServer):
    """A server for shutters controlled by pulser TTL outputs.

    The corresponding TTL channels should be set to the manual mode, with the manual inversion
    set correctly. For example, to control SR474 shutter drivers, manual inversion should be
    set to True, as the shutter driver default is TTL high.
    """

    name = "pulser_shutter_server"

    on_shutter_changed = Signal(124897, 'signal: on_shutter_changed', '(wb)')

    @inlineCallbacks
    def initServer(self):
        yield self._connect()
        self._load_config()
        self.listeners = set()

    @inlineCallbacks
    def _connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name=self.name)

    def _load_config(self):
        self.shutter_channels = PulserShutterServerConfig.shutter_channels

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, channel="w", state="b")
    def set_channel_state(self, c, channel, state):
        """Sets a shutter on or off.

        By default, True - on, False - off.
        """
        yield self.cxn.pulser.switch_manual(self.shutter_channels[channel], not state)
        notified = self.getOtherListeners(c)
        self.on_shutter_changed((channel, state), notified)

    @setting(2, channel="w", returns="b")
    def get_channel_state(self, c, channel):
        """Gets the state of a shutter."""
        is_manual, manual_state, manual_invert, auto_invert = yield self.cxn.pulser.get_state(
            self.shutter_channels[channel])
        returnValue(not manual_state)

    @setting(3, returns="*s")
    def get_channel_names(self, c):
        """Returns a list of channel names. The index of name is the channel number."""
        return self.shutter_channels


if __name__ == "__main__":
    from labrad import util
    util.runServer(PulserShutterServer())

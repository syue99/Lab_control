class phase(object):
    def __init__(self, **kw ):

        self.prev_phase = (None,)
        self.next_phase = (None,)

        self.kw = {}
        self.kw.update(kw)

        self.tstart = None
        self.tlen = None

        self.initialized = False

    def required_parameters(self):
        required_parameters = []
        for name in self.parameter_names:
            required_parameters.append((type(self).__name__,name))
        return required_parameters
    def setup(self, params):

        # first, check if all the previous phases are done
        # and find the longest of the start + len to compute our tstart

        tstart = 0

        for pl in self.prev_phase:
            if pl is not None:
                if pl.initialized == False:
                    return

                # if we get to this point, all the phases preceeding this one
                # have executed, and it's our turn. We compute what our start time
                # is based on the longest of the previous times + lengths

                new_start = pl.tstart + pl.tlen
                if new_start > tstart:
                    tstart = new_start

        # set our start time to this, and calculate our length
        self.tstart = tstart
        #change by Fred: we get the para names here to 
        self.tlen = self.getlength(params[type(self).__name__])
        self.initialized = True

        # now try to set up the following phases:
        for pl in self.next_phase:
            if pl is not None:
                pl.setup(params)

    def getlength(self, params):
        # compute length

        print("In getlength for: ", self.__class__.__name__, self.tstart)
        return 1.0

    def dophase(self, cxn, params):
        # NB: instead of passing tstart as a parameter, here, it should now be read from
        # self.tstart

        # print("Running commands for: ", self.__repr__())
        pass

    def print_checkpoint(self):
        # print("Running commands for: {:s}".format(self.__repr__()))
        pass

    def __repr__(self):
        return "%s" % self.__class__.__name__  # , repr(self.kw) if len(self.kw) > 0 else '', self.tstart)


class syncphase(phase):
    def __init__(self, **kw):
        super(syncphase, self).__init__(**kw)
        self.tsync = 0
        if 'tsync' in self.kw.keys():
            self.tsync = self.kw['tsync']
        self.period = None
        if 'period' in self.kw.keys():
            self.period = int(self.kw['period'])

    def setup(self, params):

        # first, check if all the previous phases are done
        # and find the longest of the start + len to compute our tstart

        tstart = 0

        for pl in self.prev_phase:
            if pl is not None:
                if pl.initialized == False:
                    return

                # if we get to this point, all the phases preceeding this one
                # have executed, and it's our turn. We compute what our start time
                # is based on the longest of the previous times + lengths

                new_start = pl.tstart + pl.tlen
                if new_start > tstart:
                    tstart = new_start

        # set our start time to this, and calculate our length
        if self.period is None:
            self.period = int(params['trapModulationTTLPeriod_100ns'])

        if self.tsync >= self.period:
            raise ValueError("In a synced phase: tsync needs to be less than period")

        sample_period_nicard = 0.1e-6
        curr_tstart_int = int(tstart / sample_period_nicard)
        curr_tsync = curr_tstart_int % self.period
        if curr_tsync > self.tsync:
            self.tstart = (curr_tstart_int + self.period - (curr_tsync - self.tsync)) * sample_period_nicard
        else:
            self.tstart = (curr_tstart_int + (self.tsync - curr_tsync)) * sample_period_nicard
        self.tlen = self.getlength(params)
        self.initialized = True

        # now try to set up the following phases:
        for pl in self.next_phase:
            if pl is not None:
                pl.setup(params)

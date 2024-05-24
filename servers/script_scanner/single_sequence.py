from experiment import experiment


class single_sequence(experiment):
    """Runs a single epxeriment."""

    def __init__(self, script_cls):
        """script_cls is the experiment class."""
        self.script_cls = script_cls
        super(single_sequence, self).__init__(self.script_cls.name)

    def initialize(self, cxn, context, ident):
        self.script = self.make_experiment(self.script_cls)
        self.script.initialize(cxn, context, ident)

    def run(self, cxn, context, replacement_parameters={}):
        try:
            self.script.program_main_sequence(1e-6)
        except:
            self.script._dophases()

    def finalize(self, cxn, context):
        self.script.finalize(cxn, context)

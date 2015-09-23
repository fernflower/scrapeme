class Source(object):
    def __init__(self, name, type, **kwargs):
        self.name = name
        self.type = type
        for name, value in kwargs.items():
            setattr(self, name, value)

    def to_json(self):
        import ipdb; ipdb.set_trace()

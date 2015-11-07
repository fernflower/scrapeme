class SpiderException(Exception):
    _message = "An exception in a spider has occured"

    def __init__(self, **kwargs):
        super(SpiderException, self).__init__(self._message % kwargs)


class VkSpiderException(SpiderException):
    pass


class VkAccessError(VkSpiderException):
    _message = "No access to group %(group)s"


class VkLoginFailure(VkSpiderException):
    pass


class GenerateSpiderError(SpiderException):
    pass

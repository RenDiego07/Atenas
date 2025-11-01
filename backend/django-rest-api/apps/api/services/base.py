class BaseService:
    def __init__(self):
        pass

    def perform_action(self):
        raise NotImplementedError("Subclasses should implement this method.")
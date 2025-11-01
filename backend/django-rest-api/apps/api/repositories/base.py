class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get_all(self):
        return self.model.objects.all()

    def get_by_id(self, id):
        return self.model.objects.filter(id=id).first()

    def create(self, **kwargs):
        return self.model.objects.create(**kwargs)

    def update(self, id, **kwargs):
        instance = self.get_by_id(id)
        if instance:
            for attr, value in kwargs.items():
                setattr(instance, attr, value)
            instance.save()
        return instance

    def delete(self, id):
        instance = self.get_by_id(id)
        if instance:
            instance.delete()
        return instance
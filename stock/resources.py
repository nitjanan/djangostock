from import_export import resources
from .models import ReceiveItem

class ReceiveItemResource(resources.ModelResource):
    class Meta:
        model = ReceiveItem
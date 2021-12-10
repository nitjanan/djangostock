from import_export import resources
from .models import ReceiveItem, Distributor

class ReceiveItemResource(resources.ModelResource):
    class Meta:
        model = ReceiveItem

class DistributorResource(resources.ModelResource):
    class Meta:
        model = Distributor
        fields = ('id', 'prefix__name', 'name', 'type__name', 'genre__name', 'credit__name', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated__name', 'tex', 'fax')
        
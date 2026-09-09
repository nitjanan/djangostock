from import_export import fields, resources
from .models import ReceiveItem, Distributor, UserProfile

class ReceiveItemResource(resources.ModelResource):
    class Meta:
        model = ReceiveItem

class DistributorResource(resources.ModelResource):
    class Meta:
        model = Distributor
        fields = ('id', 'prefix__name', 'name', 'type__name', 'genre__name', 'credit__name', 'discount', 'credit_limit', 'account_number', 'address', 'tel', 'payment', 'contact', 'affiliated__name', 'tex', 'fax')
        

class UserProfileResource(resources.ModelResource):
    full_name = fields.Field(column_name='ชื่อ - นามสกุล')
    position_name = fields.Field(column_name='ตำแหน่งงาน')

    class Meta:
        model = UserProfile
        export_order = ('id', 'user', 'full_name', 'position', 'position_name', 'department', 'signature', 'visible', 'branch_company')

    def dehydrate_full_name(self, obj):
        if not obj.user:
            return ""
        return "{} {}".format(obj.user.first_name, obj.user.last_name).strip()

    def dehydrate_position_name(self, obj):
        return obj.position.name if obj.position else ""

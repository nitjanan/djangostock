from stock.models import PurchaseOrder, PurchaseOrderItem
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=80)
    username = serializers.CharField(max_length=45)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def validate(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise ValidationError("Email has already been used")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()

        # Ensure Token is properly created for the user
        token, created = Token.objects.get_or_create(user=user)

        return user
    
class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ('username', 'email', 'password')
		
		extra_kwargs = {'password': {'write_only': True}}
	def create(self, validated_data):
		user = User(
			email=validated_data['email'],
			username=validated_data['username']
		)
		user.set_password(validated_data['password'])
		user.save()
		return user

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    po_ref_no = serializers.CharField(source='po.ref_no', read_only=True)
    prod_id = serializers.CharField(source='item.product.id', read_only=True)
    prod_nam = serializers.CharField(source='item.product_name', read_only=True)
    descr = serializers.CharField(source='description', read_only=True)
    unit_nam = serializers.CharField(source='unit.name', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ('po_ref_no', 'prod_id', 'prod_nam', 'descr', 'quantity', 'unit_nam', 'unit_price', 'discount', 'price')
        extra_fields = ['id']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    comp_nam = serializers.CharField(source='address_company.name_th', read_only=True)
    comp_add = serializers.CharField(source='address_company.address', read_only=True)
    comp_tel = serializers.CharField(source='address_company.tel', read_only=True)
    comp_tex = serializers.CharField(source='address_company.tex', read_only=True)
    po_type = serializers.CharField(source='po_type.name', read_only=True)
    po_type = serializers.CharField(source='po_type.name', read_only=True)
    distr_id = serializers.CharField(source='distributor.id', read_only=True)
    distr_pf = serializers.CharField(source='distributor.prefix', read_only=True)
    distr_nam = serializers.CharField(source='distributor.name', read_only=True)
    distr_add = serializers.CharField(source='distributor.address', read_only=True)
    distr_tel = serializers.CharField(source='distributor.tel', read_only=True)
    vat_type = serializers.CharField(source='vat_type.name', read_only=True)
    credit = serializers.CharField(source='credit.name', read_only=True)
    delivery = serializers.CharField(source='delivery.name', read_only=True)
    price = serializers.CharField(source='total_price', read_only=True)
    af_discount = serializers.CharField(source='total_after_discount', read_only=True)
    is_cc = serializers.CharField(source='is_cancel', read_only=True)
    cc_reason = serializers.CharField(source='cancel_reason', read_only=True)
    desc = serializers.SerializerMethodField()

    # Include the related PurchaseOrderItem objects
    items = PurchaseOrderItemSerializer(source='purchaseorderitem_set', many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ('ref_no','created', 'comp_nam', 'comp_add', 'comp_tel', 'comp_tex', 'po_type',
                   'distr_id', 'distr_pf', 'distr_nam', 'distr_add', 'distr_tel', 'vat_type', 'credit', 'shipping',
                   'desc', 'note','delivery', 'price', 'discount', 'af_discount', 'freight', 'vat', 'amount',
                   'is_cc', 'cc_reason', 'items',
                   )
        extra_fields = ['id']

    def get_desc(self, obj):
        # Get the first related PurchaseOrderItem and retrieve its car name
        first_item = obj.purchaseorderitem_set.first()  # Change if you have a related_name
        return first_item.item.requisit.car.name + first_item.item.requisit.car.code if first_item and first_item.item.requisit.car else None
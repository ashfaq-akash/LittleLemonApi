from rest_framework import serializers
from .models import MenuItem  # replace YourModel with your actual model
from .models import Category
from .models import Cart
from .models import Order
from .models import OrderItem
from django.contrib.auth.models import User,Group

from django.db import IntegrityError

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=['name']

class UserSerializer(serializers.ModelSerializer):
    group=GroupSerializer(read_only=True,many=True)
    class Meta:
        model=User
        fields=['id','username','email','group']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model= Category
        fields=['id','slug','title']

class MenuItemSerializer(serializers.ModelSerializer):
    category=CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True, source='category')
    class Meta:
        model = MenuItem
        fields = ['id','title','price','featured','category','category_id']
        extra_kwargs={
            'price': {'min_value': 2}
        }
class CartSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    # Use PrimaryKeyRelatedField for incoming data and MenuItemSerializer for outgoing data
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), write_only=True)
    menuitem_id = MenuItemSerializer(source='menuitem', read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'menuitem_id','quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price']
    def create(self, validated_data):
        user = self.context['request'].user  # Get the user from the context
        try:
            cart_item = Cart(user=user, **validated_data) #the line is creating a new Cart instance with the provided user and any other fields that were validated and passed in via validated_data.
            cart_item.save()
            return cart_item
        except IntegrityError:
            raise serializers.ValidationError({
                'non_field_errors': ["A cart item with this user and menu item already exists."]
            })

"""     def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({
                'non_field_errors': ["A cart item with this user and menu item already exists."]
            }) """
    
class OrderSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True,allow_null=True)
    delivery_crew_id = UserSerializer(source='delivery_crew', read_only=True)
    class Meta:
        model= Order
        fields=['id','user','delivery_crew','delivery_crew_id','status','total','date']
        
    
class OrderItemSerializer(serializers.ModelSerializer):
    order=OrderSerializer(read_only=True)
    menuitem=MenuItemSerializer(read_only=True)
    class Meta:
        model=OrderItem
        fields=['id','order','menuitem','quantity','unit_price','price']
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({
                'non_field_errors': ["A order item with this order and menu item already exists."]
            })

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except IntegrityError:
            raise serializers.ValidationError({
                'non_field_errors': ["A order item with this order and menu item already exists."]
            })
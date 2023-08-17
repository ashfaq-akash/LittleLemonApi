from django.shortcuts import render
from django.contrib.auth.models import User,Group
from django.shortcuts import get_object_or_404

# Create your views here.
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes,throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle,UserRateThrottle
from django.db import transaction
from django.core.paginator import Paginator,EmptyPage

from .models import MenuItem,Category,Cart,Order,OrderItem
from .serializers import MenuItemSerializer,UserSerializer,CategorySerializer,CartSerializer,OrderSerializer,OrderItemSerializer
from django.contrib.auth.models import User, Group


# Test: throttle test
@api_view()
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def throttle_check(request):
    return Response({"message": "Throttle check."})

#start of user & group management

#manager can add perosn to specific group
#manager can delete person from specific group
#manager can view user lists of users

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def group_users(request, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)

    if request.method == 'GET':
        users_in_group = group.user_set.all()
        serialized_users = UserSerializer(users_in_group, many=True)
        return Response(serialized_users.data)

    elif request.method == 'POST':
        username = request.data.get('username')
        if not username:
            return Response({"message": "Username not provided"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, username=username)
        group.user_set.add(user)
        message = f'User is added to {group_name} group'
        return Response({"message": message}, status=status.HTTP_201_CREATED)
    

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def group_user_detail(request, group_name, userId):
    group, _ = Group.objects.get_or_create(name=group_name)

    try:
        user = User.objects.get(pk=userId)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if user in group.user_set.all():
        group.user_set.remove(user)
        message = f'User is removed from {group_name} group'
        return Response({"message": message}, status=status.HTTP_200_OK)
    else:
        message = f'User is not in the {group_name} group'
        return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

#end of user & group management

#start category

#endpoint:/api/category
#Categories of items
#Managers post,delete,edit category items
# Users,Delivery crew only see catagories of items
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def item_category(request):
    if request.method=='GET':
        categories=Category.objects.all()
        serialized_item=CategorySerializer(categories,many=True)
        return Response(serialized_item.data,status.HTTP_200_OK)
    
    # Check if the user is either a Manager or an Admin (superuser)
    if request.method == 'POST' and (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        serialized_item = CategorySerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status=status.HTTP_201_CREATED)

    return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

# endpoint: /api/category/{categoryItem}
# allow GET for all users
# allow PUT, PATCH, DELETE only for managers and admin
# GET: Lists single category item. Return a 200 – Ok HTTP status code
# PUT, PATCH: Updates single category item
# DELETE: Deletes menu item
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def category_single(request, id):
    item = get_object_or_404(Category, pk=id)
    
    # Handle GET request
    if request.method == 'GET':
        serialized_item = CategorySerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    
    # Authorization check for Managers or Admins for PUT, PATCH, DELETE
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

    # Handle PUT request
    if request.method == 'PUT':
        serialized_item = CategorySerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_200_OK)

    # Handle PATCH request
    if request.method == 'PATCH':
        serialized_item = CategorySerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_200_OK)

    # Handle DELETE request
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)

# end of cataegories  

#start menu-items

#endpoint:/api/menu-items
#items of menus
#Managers post items
# Users,Delivery crew only see menus of items but cann't post items
#seraching based on categories and prices

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_items(request):
    if request.method=='GET':
        items=MenuItem.objects.select_related('category').all()
        #start of seraching,filtering and pagination
        category_name=request.query_params.get('category')
        to_price=request.query_params.get('to_price')
        search=request.query_params.get('to_price')
        ordering=request.query_params.get('ordering')
        perpage=request.query_params.get('perpage',default=2)
        page=request.query_params.get('page',default=1)
        if category_name:
            items=items.filter(category__title=category_name) #double underscore is used to filter linked models
        if to_price:
            items=items.filter(price__lte=to_price)
        if search:
            items=items.filter(title__istartwith=search)
        if ordering:
            ordering_fields=ordering.split(",")
            items=items.order_by(*ordering_fields)
        paginator=Paginator(items,per_page=perpage)
        try:
            items=paginator.page(number=page)
        except EmptyPage:
            items=[]
        #end of seraching,filtering and pagination
        serialized_item=MenuItemSerializer(items,many=True)
        return Response(serialized_item.data,status.HTTP_200_OK)
    
    # Check if the user is either a Manager or an Admin (superuser)
    if request.method == 'POST' and (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        serialized_item = MenuItemSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status=status.HTTP_201_CREATED)

    return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)


# endpoint: /api/menu-items/{menuItem}
# allow GET for all users
# allow PUT, PATCH, DELETE only for managers and admin
# GET: Lists single menu items. Return a 200 – Ok HTTP status code
# PUT, PATCH: Updates single menu item
# DELETE: Deletes menu item
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_single(request, id):
    item = get_object_or_404(MenuItem, pk=id)
    
    # Handle GET request
    if request.method == 'GET':
        serialized_item = MenuItemSerializer(item)
        return Response(serialized_item.data, status.HTTP_200_OK)
    
    # Authorization check for Managers or Admins for PUT, PATCH, DELETE
    if not (request.user.groups.filter(name='Manager').exists() or request.user.is_superuser):
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

    # Handle PUT request
    if request.method == 'PUT':
        serialized_item = MenuItemSerializer(item, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_200_OK)

    # Handle PATCH request
    if request.method == 'PATCH':
        serialized_item = MenuItemSerializer(item, data=request.data, partial=True)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_200_OK)

    # Handle DELETE request
    if request.method == 'DELETE':
        item.delete()
        return Response(status.HTTP_204_NO_CONTENT)

#end of menu-items

#start of cart-management

#endpoint: /api/cart/menu-items
#managers and delivery crews cannot access cart 
#customers can get all cart items
#customers can post,delete cart items

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def cart_management(request):
    # Get the current user
    current_user = request.user

    # Ensure the user is not part of 'Manager' or 'Delivery crew' groups
    if current_user.groups.filter(name__in=['manager', 'delivery-crew']).exists() or current_user.is_superuser:
        return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)

    # GET: Return current items in the cart for the current user token
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=current_user)
        serialized_items = CartSerializer(cart_items, many=True)
        return Response(serialized_items.data, status.HTTP_200_OK)

    # POST: Add the menu item to the cart
    if request.method == 'POST':
        serialized_item = CartSerializer(data=request.data, context={'request': request})
        if serialized_item.is_valid():
            serialized_item.save()
            return Response(serialized_item.data, status=status.HTTP_201_CREATED)
        return Response(serialized_item.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE: Deletes all menu items created by the current user token
    if request.method == 'DELETE':
        cart_items = Cart.objects.filter(user=current_user)
        cart_items.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


#end of cart-management

#start of order
#endpoint: /api/orders
#Customers can see,post all orders that are created by them
#Managers can see all orders that are created by all users
#Delivery crews can see the orders that are assigned to them

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_management(request):
    user=request.user
    # For GET requests
    if request.method=='GET':
        if request.user.groups.filter(name='manager').exists():
            orders=Order.objects.all()
        elif request.user.groups.filter(name='delivery-crew').exists(): 
            orders = Order.objects.filter(delivery_crew=user)
        else:
            orders = Order.objects.filter(user=user)

        serializer=OrderSerializer(orders,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK) 
    
    #Customer POST
    elif request.method=='POST':
    # Ensure the user is not part of 'Manager' or 'Delivery crew' groups
        if user.groups.filter(name__in=['manager', 'delivery-crew']).exists() or user.is_superuser:
            return Response({"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN)
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"message": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():  #to ensure database operations for creating an order and clearing the cart happen atomically. If one fails, none of the changes inside the block will be committed to the database.
            order = Order(user=user, total=sum([item.price for item in cart_items]))
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
            cart_items.delete()

        serialized_order = OrderSerializer(order)
        return Response(serialized_order.data, status=status.HTTP_201_CREATED)

#endpoint: /api/orders/{orderID}
#Customers can see their orders,delivery crew and order status
#Managers can see order,assign delivery crew and delete the order
#Delivery crews can see their orders that are assigned to them and they can update the status
#Delivery crews who have no orders cannot see the order details
@api_view(['PUT', 'PATCH', 'DELETE', 'GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def order_detail(request, orderId):
    # Fetch the order
    order = get_object_or_404(Order, pk=orderId)

    # Ensure the current user is the one making the request
    current_user = request.user

    if request.method=='GET' and order.user==current_user:
        serializer=OrderSerializer(order)
        return Response(serializer.data)
    
    # GET for managers to see the orders of users
    elif request.method == 'GET' and current_user.groups.filter(name="manager").exists():
            serializer = OrderSerializer(order)
            return Response(serializer.data)

    # GET for Delivery Crew to see the orders assigned to them
    elif request.method == 'GET' and current_user.groups.filter(name="delivery-crew").exists():
        if order.delivery_crew == current_user:
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        else:
            return Response({"error": "This order is not assigned to you."}, status=status.HTTP_403_FORBIDDEN)

    # PUT and PATCH for Manager
    elif request.method in ['PUT', 'PATCH'] and current_user.groups.filter(name="manager").exists():
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE for Manager
    elif request.method == 'DELETE' and current_user.groups.filter(name="manager").exists():
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH for Delivery Crew
    elif request.method == 'PATCH' and current_user.groups.filter(name="delivery-crew").exists():
        if "status" in request.data and request.data["status"] in [0, 1]:
            order.status = request.data["status"]
            order.save()
            return Response(OrderSerializer(order).data)
        else:
            return Response({"error": "Invalid or missing order status."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)


#end of order



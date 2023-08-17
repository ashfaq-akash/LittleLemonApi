from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

class Category(models.Model):
    slug = models.SlugField(blank=True)
    title = models.CharField(max_length=255, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

class MenuItem(models.Model):
    title=models.CharField(max_length=255,db_index=True)
    price=models.DecimalField(max_digits=6,decimal_places=2,db_index=True)
    featured=models.BooleanField(db_index=True)
    category=models.ForeignKey(Category,on_delete=models.PROTECT)


class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    menuitem=models.ForeignKey(MenuItem,on_delete=models.CASCADE)
    quantity=models.SmallIntegerField()
    unit_price=models.DecimalField(max_digits=6,decimal_places=2,editable=False) # Derived from MenuItem
    price=models.DecimalField(max_digits=6,decimal_places=2) #multiply the quantity with unit_price and save the result

    def save(self, *args, **kwargs):
        self.unit_price = self.menuitem.price
        self.price = self.quantity * self.unit_price
        super(Cart, self).save(*args, **kwargs)

    class Meta:
        unique_together=('menuitem','user')
    

class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    delivery_crew=models.ForeignKey(User,on_delete=models.SET_NULL,related_name="delivery_crew",null=True) #models.SET_NULL means that if a User is deleted, the delivery_crew field in the related model instances will be set to NULL.
    status=models.BooleanField(db_index=True,default=0)
    total=models.DecimalField(max_digits=6,decimal_places=2)
    date=models.DateTimeField(default=timezone.now,db_index=True)


class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    menuitem=models.ForeignKey(MenuItem,on_delete=models.CASCADE)
    quantity=models.SmallIntegerField()
    unit_price=models.DecimalField(max_digits=6,decimal_places=2)
    price=models.DecimalField(max_digits=6,decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super(OrderItem, self).save(*args, **kwargs)

    class Meta:
        unique_together=('order','menuitem')
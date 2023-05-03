from django.shortcuts import render,redirect
from .models import User,Product,Wishlist,Cart
import stripe
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone

stripe.api_key = settings.STRIPE_PRIVATE_KEY
YOUR_DOMAIN = 'http://localhost:8000'


def myorder(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=True)
	request.session['order_count']=len(carts)
	return render(request,'myorder.html',{'carts':carts})


@csrf_exempt
def create_checkout_session(request):
	amount = int(json.load(request)['post_data'])
	final_amount=amount*100
	
	session = stripe.checkout.Session.create(
		payment_method_types=['card'],
		line_items=[{
			'price_data': {
				'currency': 'inr',
				'product_data': {
					'name': 'Checkout Session Data',
					},
				'unit_amount': final_amount,
				},
			'quantity': 1,
			}],
		mode='payment',
		success_url=YOUR_DOMAIN + '/success.html',
		cancel_url=YOUR_DOMAIN + '/cancel.html',)
	return JsonResponse({'id': session.id})

def home(request):
	return render(request,'checkout1.html')

def success(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=False)
	for i in carts:
		i.payment_status=True
		i.ordered_date=timezone.now()
		i.save()
		product=Product.objects.get(id=i.product.id)
		product.cart_status=False
		product.save()
		
	carts=Cart.objects.filter(user=user,payment_status=False)
	request.session['cart_count']=len(carts)
	return render(request,'success.html')

def cancel(request):
	return render(request,'cancel.html')


def index(request):
	try:
		user=User.objects.get(email=request.session['email'])
		if user.usertype=="buyer":
			products=Product.objects.all()
			carts=Cart.objects.filter(user=user,payment_status=False)
			return render(request,'index.html',{'products':products,'carts':carts})
		else:
			return render(request,'seller-index.html')
	except:
		products=Product.objects.all()
		return render(request,'index.html',{'products':products})

def seller_index(request):
	return render(request,'seller-index.html')

def signup(request):
	if request.method=="POST":
		try:
			user=User.objects.get(email=request.POST['email'])
			msg="Email Already Registered"
			return render(request,'signup.html',{'msg':msg})
		except:
			if request.POST['password']==request.POST['cpassword']:
				User.objects.create(
						usertype=request.POST['usertype'],
						fname=request.POST['fname'],
						lname=request.POST['lname'],
						email=request.POST['email'],
						mobile=request.POST['mobile'],
						address=request.POST['address'],
						password=request.POST['password'],
						profile_pic=request.FILES['profile_pic']
					)
				msg="User Registered Successfully"
				return render(request,'signup.html',{'msg':msg})
			else:
				msg="Password & Confirm Password Dos Not Matched"
				return render(request,'signup.html',{'msg':msg})
	else:
		return render(request,'signup.html')

def login(request):
	try:
		user=User.objects.get(email=request.POST['email'])
		if user.password==request.POST['password']:
			if user.usertype=="buyer":
				request.session['email']=user.email
				request.session['fname']=user.fname
				request.session['profile_pic']=user.profile_pic.url
				wishlists=Wishlist.objects.filter(user=user)
				request.session['wishlist_count']=len(wishlists)
				carts=Cart.objects.filter(user=user,payment_status=False)
				request.session['cart_count']=len(carts)
				return redirect('index')
			else:
				request.session['email']=user.email
				request.session['fname']=user.fname
				request.session['profile_pic']=user.profile_pic.url
				return render(request,'seller-index.html')
		else:
			msg="Incorrect Password"
			return render(request,'login.html',{'msg':msg})
	except Exception as e:
		print(e)
		msg="Email Not Registered"
		return render(request,'login.html',{'msg':msg})
	return render(request,'login.html')

def logout(request):
	try:
		del request.session['email']
		del request.session['fname']
		del request.session['profile_pic']
		return render(request,'login.html')
	except:
		return render(request,'login.html')

def change_password(request):
	user=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		if user.password==request.POST['old_password']:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				if user.usertype=="buyer":
					carts=Cart.objects.filter(user=user)
					msg="New Password & Confirm New Password Does Not Matched"
					return render(request,'change-password.html',{'msg':msg,'carts':carts})
				else:
					msg="New Password & Confirm New Password Does Not Matched"
					return render(request,'seller-change-password.html',{'msg':msg})
		else:
			if user.usertype=="buyer":
				carts=Cart.objects.filter(user=user)
				msg="Old Password Does Not Matched"
				return render(request,'change-password.html',{'msg':msg,'carts':carts})
			else:
				msg="Old Password Does Not Matched"
				return render(request,'seller-change-password.html',{'msg':msg})
	else:
		if user.usertype=="buyer":
			return render(request,'change-password.html')
		else:
			return render(request,'seller-change-password.html')

def profile(request):
	user=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		user.fname=request.POST['fname']
		user.lname=request.POST['lname']
		user.mobile=request.POST['mobile']
		user.address=request.POST['address']
		try:
			user.profile_pic=request.FILES['profile_pic']
		except:
			pass
		user.save()
		request.session['profile_pic']=user.profile_pic.url
		msg="Profile Updated Successfully"
		if user.usertype=="buyer":
			carts=Cart.objects.filter(user=user)
			return render(request,'profile.html',{'user':user,'msg':msg,'carts':carts})
		else:
			return render(request,'seller-profile.html',{'user':user,'msg':msg})
	else:
		user=User.objects.get(email=request.session['email'])
		if user.usertype=="buyer":
			carts=Cart.objects.filter(user=user)
			return render(request,'profile.html',{'user':user,'carts':carts})
		else:
			return render(request,'seller-profile.html',{'user':user})

def seller_add_product(request):
	if request.method=="POST":
		seller=User.objects.get(email=request.session['email'])
		Product.objects.create(
				seller=seller,
				product_category=request.POST['product_category'],
				product_name=request.POST['product_name'],
				product_desc=request.POST['product_desc'],
				product_price=request.POST['product_price'],
				product_image=request.FILES['product_image']
			)
		msg="Product Added Successfully"
		return render(request,'seller-add-product.html',{'msg':msg})
	else:
		return render(request,'seller-add-product.html')

def seller_view_product(request):
	seller=User.objects.get(email=request.session['email'])
	products=Product.objects.filter(seller=seller)
	return render(request,'seller-view-product.html',{'products':products})

def seller_product_detail(request,pk):
	product=Product.objects.get(pk=pk)
	return render(request,'seller-product-detail.html',{'product':product})

def seller_edit_product(request,pk):
	product=Product.objects.get(pk=pk)
	if request.method=="POST":
		product.product_category=request.POST['product_category']
		product.product_name=request.POST['product_name']
		product.product_desc=request.POST['product_desc']
		product.product_price=request.POST['product_price']
		try:
			product.product_image=request.FILES['product_image']
		except:
			pass
		product.save()
		msg="Product Updated Successfully"
		return render(request,'seller-edit-product.html',{'product':product,'msg':msg})
	else:
		return render(request,'seller-edit-product.html',{'product':product})

def seller_delete_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	return redirect("seller-view-product")

def laptops(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	products=Product.objects.filter(product_category="Laptop")
	return render(request,'index.html',{'products':products,'carts':carts})

def Accessories(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	products=Product.objects.filter(product_category="Accessories")
	return render(request,'index.html',{'products':products,'carts':carts})

def Camera(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	products=Product.objects.filter(product_category="Camera")
	return render(request,'index.html',{'products':products,'carts':carts})

def product_details(request,pk):
	wishlist_flag=False
	cart_flag=False
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	try:
		Wishlist.objects.get(user=user,product=product)
		wishlist_flag=True
	except:
		pass
	try:
		Cart.objects.get(user=user,product=product)
		cart_flag=True
	except:
		pass
	return render(request,'product-detail.html',{'product':product,'wishlist_flag':wishlist_flag,'cart_flag':cart_flag,'carts':carts})

def add_to_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	product.wishlist_status=True
	product.save()
	user=User.objects.get(email=request.session['email'])
	Wishlist.objects.create(user=user,product=product)
	return redirect('wishlist')

def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	wishlists=Wishlist.objects.filter(user=user)
	request.session['wishlist_count']=len(wishlists)
	return render(request,'wishlist.html',{'wishlists':wishlists,'carts':carts})

def remove_from_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	product.wishlist_status=False
	product.save()
	user=User.objects.get(email=request.session['email'])
	wishlist=Wishlist.objects.get(user=user,product=product)
	wishlist.delete()
	return redirect('wishlist')

def cart(request):
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user,payment_status=False)
	request.session['cart_count']=len(carts)
	return render(request,'cart.html',{'carts':carts})

def add_to_cart(request,pk):
	product=Product.objects.get(pk=pk)
	product.cart_status=True
	product.save()
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(
		user=user,
		product=product,
		product_price=product.product_price,
		product_qty=1,
		total_price=product.product_price
		)
	return redirect('cart')

def remove_from_cart(request,pk):
	product=Product.objects.get(pk=pk)
	product.cart_status=False
	product.save()
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.get(user=user,product=product)
	cart.delete()
	return redirect('cart')

def checkout(request):
	net_price=0
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	for i in carts:
		net_price=net_price+i.total_price
	return render(request,'checkout.html',{'carts':carts,'user':user,'net_price':net_price})
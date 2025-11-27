from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms_address import AddressForm
from .models_address import Address

@login_required
def save_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.save()
            return redirect('accounts:select_address')
    else:
        last_address = Address.objects.filter(user=request.user).last()
        form = AddressForm(instance=last_address)
    return render(request, 'accounts/address_form.html', {'form': form})

@login_required
def select_address(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/select_address.html', {'addresses': addresses})

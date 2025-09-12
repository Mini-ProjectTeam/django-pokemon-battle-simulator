from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from .forms import CustomUserCreationForm
from .models import User

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

class ProfileUpdateView(UpdateView):
    model = User
    fields = ['profile_image', 'status_message']
    template_name = 'profile_update.html'
    success_url = reverse_lazy('my_info') # '내 정보' 페이지 URL 이름


    def get_object(self):
        return self.request.user
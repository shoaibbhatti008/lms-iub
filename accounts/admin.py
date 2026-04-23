from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from .models import CustomUser

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True, label='Role', initial='student')
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        
        # Set permissions based on role
        if user.role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user.role == 'teacher':
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False
        
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # Make sure add permission is enabled
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'bio', 'profile_pic')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # These methods ensure add permission is granted
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ['role', 'is_superuser', 'is_staff']
        return []

# Register the admin class
admin.site.register(CustomUser, CustomUserAdmin)

# Customize admin site header
admin.site.site_header = "LMS Administration"
admin.site.site_title = "LMS Admin Portal"
admin.site.index_title = "Welcome to LMS Admin Panel"

# pipes/admin_customization.py
from django.contrib import admin
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required

class CustomAdminSite(admin.AdminSite):
    site_header = "SP Auto Parts Solution - Admin"
    site_title = "SP Auto Parts Solution"
    index_title = "Welcome to SP Auto Parts Solution Admin"
    
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)
        
        # Sort the apps alphabetically
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        
        # Sort the models alphabetically within each app
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
        
        return app_list
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        context['site_url'] = '/'
        return context

# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')
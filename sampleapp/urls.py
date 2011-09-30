# This also imports the include function
from django.conf.urls.defaults import patterns, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('polls.urls')),
    (r'^admin/', include(admin.site.urls)),

)
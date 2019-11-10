from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf.urls.static import static
from blog.sitemaps import PostSitemap, BlogSitemap
from portfolio.sitemaps import PortfolioSitemap
from diaries.sitemaps import DiarySitemap

sitemaps = {
    'posts': PostSitemap,
    'blog': BlogSitemap,
    'portfolio': PortfolioSitemap,
    'diary': DiarySitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('blog/', include('blog.urls')),
    path('diaries/', include('diaries.urls')),
    path('', include('portfolio.urls')),
]

# 開発環境でのメディアファイルの配信設定
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

from django.contrib.sitemaps import Sitemap
from django.shortcuts import resolve_url


class PortfolioSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['portfolio:top']

    def location(self, obj):
        return resolve_url(obj)

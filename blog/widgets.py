from django import forms
from django.urls import reverse_lazy


class SuggestPostWidget(forms.SelectMultiple):
    template_name = 'blog/widgets/suggest.html'

    class Media:
        css = {
            'all': [
                'blog/css/admin_post_form.css',

            ]
        }
        js = ['blog/js/suggest.js']

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if 'class' in self.attrs:
            self.attrs['class'] += ' suggest'
        else:
            self.attrs['class'] = 'suggest'


class SimpleMDE(forms.Textarea):

    class Media:
        css = {
            'all': [
                'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css',

            ]
        }
        js = [
            'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js',
            'blog/js/markdown_init.js'
        ]

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if 'class' in self.attrs:
            self.attrs['class'] += ' markdown'
        else:
            self.attrs['class'] = 'markdown'


class AdminSimpleMDE(SimpleMDE):

    class Media:
        css = {
            'all': [
                'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css',

            ]
        }
        js = [
            'https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js',
            'blog/js/markdown_init.js',
            'blog/js/csrf.js',
            'blog/js/upload.js'
        ]

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs['data-url'] = reverse_lazy('blog:api_image_upload')

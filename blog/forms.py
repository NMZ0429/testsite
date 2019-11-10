from django import forms
from django.db import models
from django.core.files.storage import default_storage
from django.urls import reverse_lazy
from .fields import SimpleCaptchaField
from .models import Comment, Reply, Tag, Post, EmailPush
from .widgets import SuggestPostWidget, SimpleMDE, AdminSimpleMDE


TITLE_CONTAIN = '1'
TEXT_CONTAIN = '2'
TITLE_OR_TEXT_CONTAIN = '3'
COMMENT_CONTAIN = '4'

AND = '1'
OR = '2'


class PostSearchForm(forms.Form):
    """記事検索フォーム。"""
    key_word = forms.CharField(
        label='検索キーワード',
        required=False,
    )

    search_kind = forms.ChoiceField(
        label='キーワード検索タイプ',
        required=False,
        choices=[
            (TITLE_OR_TEXT_CONTAIN, 'タイトルか本文に含む'), (TITLE_CONTAIN, 'タイトルに含む'),
            (TEXT_CONTAIN, '本文に含む'), (COMMENT_CONTAIN, 'コメントに含む'),
        ],
    )

    search_tags = forms.ModelMultipleChoiceField(
        label='タグでの絞り込み',
        required=False,
        queryset=Tag.objects.annotate(post_count=models.Count('post')).order_by('name'),
    )

    search_tags_kind = forms.ChoiceField(
        label='タグの検索タイプ',
        required=False,
        choices=[(AND, 'AND'), (OR, 'OR')],
    )

    page_nums = forms.IntegerField(
        label='1ページの表示件数',
        required=False,
        min_value=1,
    )


class AdminPostCreateForm(forms.ModelForm):
    """記事の作成・更新フォーム"""

    class Meta:
        model = Post
        fields = ['title', 'is_public', 'description', 'keywords', 'text', 'relation_posts', 'tags']
        widgets = {
            'text': AdminSimpleMDE,
            'relation_posts': SuggestPostWidget(attrs={'data-url': reverse_lazy('blog:api_posts_suggest')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.annotate(
            post_count=models.Count('post')
        ).order_by('name')


class CommentCreateForm(forms.ModelForm):
    """コメント投稿フォーム"""
    captcha = SimpleCaptchaField()

    class Meta:
        model = Comment
        fields = ('name', 'text', 'email')
        widgets = {
            'text': SimpleMDE,
        }


class ReplyCreateForm(forms.ModelForm):
    """返信コメント投稿フォーム"""
    captcha = SimpleCaptchaField()

    class Meta:
        model = Reply
        fields = ('name', 'text')
        widgets = {
            'text': SimpleMDE,
        }


class EmailForm(forms.ModelForm):
    """Eメール通知の登録用フォーム"""

    class Meta:
        model = EmailPush
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email']
        EmailPush.objects.filter(email=email, is_active=False).delete()
        return email


class FileUploadForm(forms.Form):
    """ファイルのアップロードフォーム"""
    file = forms.FileField()

    def save(self):
        upload_file = self.cleaned_data['file']
        file_name = default_storage.save(upload_file.name, upload_file)
        file_url = default_storage.url(file_name)
        return file_url

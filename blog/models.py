from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.shortcuts import resolve_url
from django.template.loader import render_to_string


class Tag(models.Model):
    name = models.CharField('タグ名', max_length=255, unique=True)

    def __str__(self):
        if hasattr(self, 'post_count'):
            return f'{self.name}({self.post_count})'
        else:
            return self.name


class Post(models.Model):
    """記事"""
    title = models.CharField('タイトル', max_length=32)
    text = models.TextField('本文')
    tags = models.ManyToManyField(Tag, verbose_name='タグ', blank=True)

    relation_posts = models.ManyToManyField('self', verbose_name='関連記事', blank=True)
    is_public = models.BooleanField('公開可能か?', default=True)
    description = models.TextField('記事の説明', max_length=130)
    keywords = models.CharField('記事のキーワード', max_length=255, default='記事のキーワード')
    created_at = models.DateTimeField('作成日', auto_now_add=True)
    updated_at = models.DateTimeField('更新日', auto_now=True)

    def __str__(self):
        return self.title

    def line_push(self, request):
        """記事をラインで通知"""
        if settings.USE_LINE_BOT:
            import linebot
            from linebot.models import TextSendMessage
            context = {
                'post': self,
            }
            message = render_to_string('blog/mail/send_latest_notify_message.txt', context, request)
            line_bot_api = linebot.LineBotApi(settings.LINE_BOT_API_KEY)
            for push in LinePush.objects.all():
                line_bot_api.push_message(push.user_id, messages=TextSendMessage(text=message))

    def email_push(self, request):
        """記事をメールで通知"""
        context = {
            'post': self,
        }
        subject = render_to_string('blog/mail/send_latest_notify_subject.txt', context, request)
        message = render_to_string('blog/mail/send_latest_notify_message.txt', context, request)

        from_email = settings.DEFAULT_FROM_EMAIL
        bcc = [settings.DEFAULT_FROM_EMAIL]
        for mail_push in EmailPush.objects.filter(is_active=True):
            bcc.append(mail_push.email)
        email = EmailMessage(subject, message, from_email, [], bcc)
        email.send()

    def browser_push(self):
        """記事をブラウザ通知"""
        if settings.USE_WEB_PUSH:
            import requests
            data = {
                'app_id': settings.ONE_SIGNAL_APP_ID,
                'included_segments': ['All'],
                'contents': {'en': self.title},
                'headings': {'en': 'Naritoブログ'},
                'url': resolve_url('blog:post_detail', pk=self.pk),
            }
            requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers={'Authorization': settings.ONE_SIGNAL_REST_KEY},
                json=data,
            )


class Comment(models.Model):
    """記事に紐づくコメント"""
    name = models.CharField('名前', max_length=255, default='名無し')
    text = models.TextField('本文')
    email = models.EmailField('メールアドレス', blank=True, help_text='入力しておくと、返信があった際に通知します。コメント欄には表示されません。')
    target = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='対象記事')
    created_at = models.DateTimeField('作成日', auto_now_add=True)

    def __str__(self):
        return self.text[:20]


class Reply(models.Model):
    """コメントに紐づく返信"""
    name = models.CharField('名前', max_length=255, default='名無し')
    text = models.TextField('本文')
    target = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='対象コメント')
    created_at = models.DateTimeField('作成日', auto_now_add=True)

    def __str__(self):
        return self.text[:20]


class LinePush(models.Model):
    """Lineでのプッシュ先を表す"""
    user_id = models.CharField('ユーザーID', max_length=100, unique=True)

    def __str__(self):
        return self.user_id


class EmailPush(models.Model):
    """メールでのプッシュ先を表す"""
    email = models.EmailField('メールアドレス', unique=True)
    is_active = models.BooleanField('有効フラグ', default=False)

    def __str__(self):
        return self.email

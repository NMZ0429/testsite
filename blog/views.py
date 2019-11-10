import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.db.models import Q, Count
from django.http import Http404, JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from .forms import (
    PostSearchForm, CommentCreateForm, ReplyCreateForm,
    TITLE_CONTAIN, TEXT_CONTAIN, TITLE_OR_TEXT_CONTAIN, EmailForm, AND,
    FileUploadForm, COMMENT_CONTAIN
)
from .models import Post, Tag, Comment, Reply, EmailPush, LinePush


class PublicPostIndexView(generic.ListView):
    """公開記事の一覧を表示する。"""
    paginate_by = 10
    model = Post

    def get_queryset(self):
        queryset = super().get_queryset()
        self.request.form = form = PostSearchForm(self.request.GET)
        form.is_valid()

        tags = form.cleaned_data.get('search_tags')
        search_kind = form.cleaned_data.get('search_kind')
        key_word = form.cleaned_data.get('key_word')
        page_nums = form.cleaned_data.get('page_nums')
        search_tags_kind = form.cleaned_data.get('search_tags_kind')

        # タグを選択していれば、それで絞り込む
        if tags:
            if search_tags_kind == AND:
                for tag in tags:
                    queryset = queryset.filter(tags=tag)
            else:
                queryset = queryset.filter(tags__in=tags)

        # キーワードが入力されていれば、いずれかの方法で絞り込む
        # キーワードが半角スペースで区切られていれば、その回数だけfilterします。つまりANDです。
        if key_word:
            # タイトルに含む
            if search_kind == TITLE_CONTAIN:
                for word in key_word.split():
                    queryset = queryset.filter(title__icontains=word)

            # 本文に含む
            elif search_kind == TEXT_CONTAIN:
                for word in key_word.split():
                    queryset = queryset.filter(text__icontains=word)

            # タイトルか本文に含む
            elif search_kind == TITLE_OR_TEXT_CONTAIN:
                for word in key_word.split():
                    queryset = queryset.filter(Q(title__icontains=word) | Q(text__icontains=word))

            # コメントに含む
            elif search_kind == COMMENT_CONTAIN:
                comment_list = Comment.objects.all()
                for word in key_word.split():
                    comment_list = comment_list.filter(Q(text__icontains=word) | Q(name__icontains=word))

                reply_list = Reply.objects.all()
                for word in key_word.split():
                    reply_list = reply_list.filter(Q(text__icontains=word) | Q(name__icontains=word))

                post_ids = {comment.target.pk for comment in comment_list} | {reply.target.target.pk for reply in reply_list}
                queryset = queryset.filter(id__in=post_ids)

        # 表示件数の指定があれば
        if page_nums:
            self.paginate_by = page_nums

        queryset = queryset.filter(
            is_public=True
        ).order_by('-created_at').prefetch_related('tags')
        return queryset


class PrivatePostIndexView(LoginRequiredMixin, generic.ListView):
    """非公開の記事一覧を表示する。"""
    model = Post

    def get_queryset(self):
        queryset = Post.objects.filter(
            is_public=False
        ).order_by('-created_at').prefetch_related('tags')
        return queryset


class PostDetailView(generic.DetailView):
    """記事詳細ページを表示する。"""
    model = Post

    def get_queryset(self):
        return super().get_queryset().prefetch_related('tags', 'comment_set__reply_set')

    def get_object(self, queryset=None):
        """その記事が公開か、ユーザがログインしていれば表示する。"""
        post = super().get_object()
        if post.is_public or self.request.user.is_authenticated:
            return post
        else:
            raise Http404


class CommentCreate(generic.CreateView):
    """記事へのコメント作成ビュー。"""
    model = Comment
    form_class = CommentCreateForm

    def form_valid(self, form):
        post_pk = self.kwargs['pk']
        post = get_object_or_404(Post, pk=post_pk)
        comment = form.save(commit=False)
        comment.target = post
        comment.request = self.request
        comment.save()
        messages.info(self.request, 'コメントしました。')
        return redirect('blog:post_detail', pk=post_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post, pk=self.kwargs['pk'])
        return context


class ReplyCreate(generic.CreateView):
    """コメントへの返信作成ビュー。"""
    model = Reply
    form_class = ReplyCreateForm
    template_name = 'blog/comment_form.html'

    def form_valid(self, form):
        comment_pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=comment_pk)
        reply = form.save(commit=False)
        reply.target = comment
        reply.request = self.request
        reply.save()
        messages.info(self.request, '返信しました。')
        return redirect('blog:post_detail', pk=comment.target.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_pk = self.kwargs['pk']
        comment = get_object_or_404(Comment, pk=comment_pk)
        context['post'] = comment.target
        return context


def subscribe(request):
    """ブログの購読ページ"""
    form = EmailForm(request.POST or None)
    # メール購読の処理
    if request.method == 'POST' and form.is_valid():
        push = form.save()
        context = {
            'token': dumps(push.pk),
        }
        subject = render_to_string('blog/mail/confirm_push_subject.txt', context, request)
        message = render_to_string('blog/mail/confirm_push_message.txt', context, request)

        from_email = settings.DEFAULT_FROM_EMAIL
        to = [push.email]
        bcc = [settings.DEFAULT_FROM_EMAIL]
        email = EmailMessage(subject, message, from_email, to, bcc)
        email.send()

        return redirect('blog:subscribe_thanks')

    context = {
        'form': form,
        'USE_LINE_BOT': settings.USE_LINE_BOT,
        'USE_WEB_PUSH': settings.USE_WEB_PUSH,
    }
    if settings.USE_WEB_PUSH:
        context['ONE_SIGNAL_APP_ID'] = settings.ONE_SIGNAL_APP_ID

    return render(request, 'blog/subscribe.html', context)


def subscribe_thanks(request):
    """メール購読ありがとう、確認メール送ったよページ"""
    return render(request, 'blog/subscribe_thanks.html')


def subscribe_register(request, token):
    """メール購読の確認処理"""
    try:
        user_pk = loads(token, max_age=60*60*24)  # 1日以内

    # 期限切れ
    except SignatureExpired:
        return HttpResponseBadRequest()

    # tokenが間違っている
    except BadSignature:
        return HttpResponseBadRequest()

    # tokenは問題なし
    else:
        try:
            push = EmailPush.objects.get(pk=user_pk)
        except EmailPush.DoesNotExist:
            return HttpResponseBadRequest()
        else:
            if not push.is_active:
                # まだ仮登録で、他に問題なければ本登録とする
                push.is_active = True
                push.save()
                return redirect('blog:subscribe_done')

    return HttpResponseBadRequest()


def subscribe_done(request):
    """メール購読完了"""
    return render(request, 'blog/subscribe_done.html')


@csrf_exempt
def line_callback(request):
    """ラインの友達追加時に呼び出され、ラインのIDを登録する。"""
    if request.method == 'POST':
        request_json = json.loads(request.body.decode('utf-8'))
        line_user_id = request_json['events'][0]['source']['userId']
        LinePush.objects.create(user_id=line_user_id)
    return HttpResponse()


def api_image_upload(request):
    """ファイルのアップロード用ビュー"""
    form = FileUploadForm(files=request.FILES)
    if form.is_valid():
        url = form.save()
        return JsonResponse({'url': url})
    return HttpResponseBadRequest()


def api_posts_suggest(request):
    """サジェスト候補の記事をJSONで返す。"""
    keyword = request.GET.get('keyword')
    if keyword:
        post_list = [{'pk': post.pk, 'name': str(post)} for post in Post.objects.filter(title__icontains=keyword)]
    else:
        post_list = []
    return JsonResponse({'object_list': post_list})

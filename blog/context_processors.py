from .forms import PostSearchForm


def common(request):
    if hasattr(request, 'form'):
        form = request.form
    else:
        form = PostSearchForm(request.GET)

    context = {
        'search_form': form,
    }
    return context

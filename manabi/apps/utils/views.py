from django.views.generic import TemplateView, RedirectView


def direct_to_template(template=None):
    return TemplateView.as_view(template_name=template)

def redirect_to(url=None):
    return RedirectView.as_view(url=url)


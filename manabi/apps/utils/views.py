from django.views.generic import TemplateView


def direct_to_template(template=None):
    return TemplateView.as_view(template_name=template)


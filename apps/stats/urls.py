from django.conf.urls.defaults import *


# graph data urls
graph_urlpatterns = patterns('stats.views',
    url(r'^repetitions.json$',
        'repetitions',
        name='graphs_repetitions'),
)


# place app url patterns here
urlpatterns = patterns('stats.views',
    url(r'^graphs/', include(graph_urlpatterns)),
)


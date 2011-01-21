from django.conf.urls.defaults import *


# graph data urls
graph_urlpatterns = patterns('stats.views',
    url(r'^repetitions.json$',
        'repetitions',
        name='graphs_repetitions'),
    url(r'^due_counts.json$',
        'due_counts',
        name='graphs_due_counts'),
)


# place app url patterns here
urlpatterns = patterns('stats.views',
    url(r'^graphs/', include(graph_urlpatterns)),

    url(r'^scheduling-summary/$',
        'scheduling_summary',
        name='stats_scheduling_summary'),

    url(r'^$', 'index', name='stats'),
)


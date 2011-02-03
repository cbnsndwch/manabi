from django.conf.urls.defaults import *


# graph data urls
graph_urlpatterns = patterns('stats.views',
    url(r'^repetitions.json$',
        'repetitions',
        name='graphs_repetitions'),
    url(r'^due_counts.json$',
        'due_counts',
        name='graphs_due_counts'),

    url(r'^usage_history.json$',
        'usage_history',
        name='graphs_usage_history'),
)



# place app url patterns here
urlpatterns = patterns('stats.views',
    url(r'^graphs/', include(graph_urlpatterns)),

    url(r'^scheduling-summary/$',
        'scheduling_summary',
        name='stats_scheduling_summary'),

    url(r'^cards/(?P<card_id>\d+).json$', 'card_stats_json',
        name='api-card_stats'),

    url(r'^cards/(?P<card_id>\d+)/$', 'card_stats',
        name='card_stats'),

    url(r'^$', 'index', name='stats'),
)


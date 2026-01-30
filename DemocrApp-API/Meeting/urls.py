from django.urls import path
from . import views
from .views import reports

urlpatterns = [
    path('<int:meeting_id>/checktoken', views.check_token, name='meeting/token_check'),
    path('<int:meeting_id>', views.meeting, name='meeting/detail'),
    path('<int:meeting_id>/new_vote', views.new_vote, name='meeting/new_vote'),
    path('<int:meeting_id>/close', views.close_meeting, name='meeting/close'),
    path('<int:meeting_id>/<int:vote_id>/open_vote', views.open_vote, name='meeting/open_vote'),
    path('<int:meeting_id>/<int:vote_id>/close_vote', views.close_vote, name='meeting/close_vote'),
    path('<int:meeting_id>/<int:vote_id>/close_vote/stv', views.close_vote_stv, name='meeting/close_vote/stv'),
    path('<int:meeting_id>/<int:vote_id>/close_vote/yna', views.close_vote_yna, name='meeting/close_vote/yna'),
    path('<int:meeting_id>/<int:vote_id>/break_tie', views.break_tie, name='meeting/break_tie'),
    path('manage/<int:meeting_id>', views.manage_meeting, name='meeting/manage'),
    path('manage/<int:meeting_id>/<int:vote_id>', views.manage_vote, name='meeting/manage_vote'),
    path('<int:meeting_id>/announcement', views.announcement, name='meeting/announcement'),
    path('manage/<int:meeting_id>/<int:vote_id>/add_option', views.add_option, name='meeting/add_vote_option'),
    path('manage/<int:meeting_id>/<int:vote_id>/remove_option', views.remove_option, name='meeting/remove_vote_option'),
    path('manage/<int:meeting_id>/<int:vote_id>/update_field', views.update_vote_field, name='meeting/update_vote_field'),
    path('manage/<int:meeting_id>/<int:vote_id>/candidates.json', views.get_ballot_candidates, name='meeting/get_ballot_candidates'),
    path('manage/<int:meeting_id>/create_token', views.create_token, name='meeting/create_token'),
    path('manage/<int:meeting_id>/deactivate_token', views.deactivate_token, name='meeting/deactivate_token'),
    path('reports', reports.report_list, name='meeting/report'),
    path('reports/<int:meeting_id>', reports.meeting_report, name='meeting/report/meeting'),
    path('reports/<int:meeting_id>.json', reports.meeting_report_json, name='meeting/report/meeting/json'),
    path('reports/<int:meeting_id>.yaml', reports.meeting_report_yaml, name='meeting/report/meeting/yaml'),
    path('reports/<int:meeting_id>/<int:vote_id>', reports.vote_report, name='meeting/report/vote'),
    path('public/vote/<uuid:public_id>/', reports.public_reports.public_vote_report, name='meeting/public_vote_report'),
    path('public/meeting/<uuid:public_id>/', reports.public_reports.public_meeting_report, name='meeting/public_meeting_report'),
    path('list', views.meeting_list, name='meeting/list'),
    path('kiosk_redirect', views.kiosk_redirect, name='meeting/kiosk_redirect')
]

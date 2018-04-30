from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # widoki logowania i zmiany hasła
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout-then-login/', auth_views.logout_then_login, name='logout_then_login'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # widok tworzenia nowego użytkownika
    path('register/', views.register, name='register'),

    # widoki edytowania danych użytkownika po zalogowaniu
    path('settings/', views.settings, name='settings'),
    path('settings/edit/', views.edit, name='edit'),

    # widok po zalogowaniu
    path('', views.index_view, name='index'),
    path('match_list/', views.MatchListView.as_view(), name='match_list'),
    path('bet_form/<int:pk>', views.bet_form_view, name='bet_form'),
    path('bet_formset/', views.bet_formset_view, name='bet_formset'),
    path('extra_bets_form/', views.extra_bets_form_view, name='extra_bets'),
    path('players_table/', views.players_table_view, name='players_table'),
    path('all_bets_list/', views.AllBetsListView.as_view(), name='all_bets_list'),
]

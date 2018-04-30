from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User, Team, Footballer, Match, GoalScorer, Bet, ExtraBets, ScoringSystem


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name', 'email')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    fields = ('name', 'short_name', 'is_champion')
    list_display = ('name', 'short_name', 'is_champion', 'created', 'updated')
    list_per_page = 10
    search_fields = ('name',)


@admin.register(Footballer)
class FootballerAdmin(admin.ModelAdmin):
    fields = ('name', 'team', 'is_top_scorer')
    list_display = ('name', 'team', 'is_top_scorer', 'created', 'updated')
    list_per_page = 10
    search_fields = ('name', 'team__name')


class GoalScorerInline(admin.TabularInline):
    model = GoalScorer
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    readonly_fields = ('available_for_betting',)
    fields = (
        ('home_team', 'home_score'),
        ('away_team', 'away_score'),
        'tournament_stage',
        'date_and_time',
        'available_for_betting',
    )
    list_display = ('date_and_time', 'tournament_stage', 'display_match',
                    'home_score', 'away_score', 'available_for_betting')
    list_editable = ('home_score', 'away_score')
    list_filter = ('date_and_time', 'tournament_stage')
    search_fields = ('home_team', 'away_team')
    date_hierarchy = 'date_and_time'
    ordering = ['date_and_time']
    inlines = [GoalScorerInline]


@admin.register(GoalScorer)
class GoalScorerAdmin(admin.ModelAdmin):
    fields = ('footballer', 'match')
    list_display = ('footballer', 'match', 'created', 'updated')
    search_fields = ('footballer__name', 'footballer__team__name')


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    readonly_fields = ('points', 'created', 'updated', 'is_editable')
    fields = ('player', 'match', 'home_score', 'away_score', 'points', 'created', 'updated', 'is_editable')
    list_display = ('player', 'match', 'display_bet', 'points', 'created', 'updated', 'is_editable')
    list_filter = ('player', 'match')
    search_fields = ('player', 'match')


@admin.register(ExtraBets)
class ExtraBetAdmin(admin.ModelAdmin):
    readonly_fields = ('points', 'created', 'updated')
    fields = ('player', 'team', 'footballer', 'points', 'created', 'updated')
    list_display = ('player', 'team', 'footballer', 'points', 'created', 'updated')
    list_filter = ('player', 'team', 'footballer')
    search_fields = ('player', 'team', 'footballer')


@admin.register(ScoringSystem)
class ScoringSystemAdmin(admin.ModelAdmin):
    fields = ('evaluated_field', 'short_name', 'result_hitted', 'goal_diff_hitted', 'direction_hitted', 'other_points')
    list_display = ('evaluated_field', 'result_hitted', 'goal_diff_hitted', 'direction_hitted', 'other_points')
    list_filter = ('evaluated_field',)
    search_fields = ('evaluated_field',)

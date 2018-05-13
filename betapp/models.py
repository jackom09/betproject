from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone


# Modification of authentication rules based on:
# www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    is_active = models.BooleanField(default=False)
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=50, blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class ScoringSystem(models.Model):
    evaluated_field = models.CharField(max_length=20)
    short_name = models.CharField(max_length=3)
    result_hitted = models.PositiveSmallIntegerField(default=0)
    goal_diff_hitted = models.PositiveSmallIntegerField(default=0)
    direction_hitted = models.PositiveSmallIntegerField(default=0)
    other_points = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('other_points', 'result_hitted', 'goal_diff_hitted', 'direction_hitted')

    def __str__(self):
        return self.evaluated_field


class Team(models.Model):
    name = models.CharField(max_length=50, unique=True)
    short_name = models.CharField(max_length=3, unique=True)
    is_champion = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for bet in ExtraBets.objects.filter(team=self):
            bet.save()


class Footballer(models.Model):
    name = models.CharField(max_length=50, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='footballers')
    is_top_scorer = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('team', 'name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for bet in ExtraBets.objects.filter(footballer=self):
            bet.save()


class Match(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    date_and_time = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tournament_stage = models.ForeignKey(ScoringSystem, on_delete=models.CASCADE,
                                         limit_choices_to={'other_points': 0})

    class Meta:
        ordering = ('date_and_time',)
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f'{self.display_match()} ({str(self.date_and_time.strftime("%d/%m/%Y, %H:%M"))})'

    def clean(self):
        if self.away_team == self.home_team:
            raise ValidationError({'home_team': 'Must be different from away team.',
                                   'away_team': 'Must be different from home team.'})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for bet in self.bets.filter(match=self):
            bet.save()

    def display_match(self):
        return f'{self.home_team.name} vs. {self.away_team.name}'
    display_match.short_description = 'Teams'

    def display_result(self):
        if self.home_score is None or self.away_score is None:
            return f'-'
        else:
            return f'{str(self.home_score)} : {str(self.away_score)}'
    display_result.short_description = 'Result'

    def total_goals(self):
        return self.home_score + self.away_score

    @property
    def available_for_betting(self):
        return self in Match.available_bet_list()

    @property
    def is_inside_date_ranges(self):
        return timezone.now() + timezone.timedelta(days=3) >= self.date_and_time > timezone.now()

    @staticmethod
    def available_bet_list():
        matches = Match.objects.all()
        list_of_teams = []
        for match in matches:
            if not match.is_inside_date_ranges or match.home_team in list_of_teams or match.away_team in list_of_teams:
                matches = matches.exclude(id=match.id)
            else:
                list_of_teams.append(match.home_team)
                list_of_teams.append(match.away_team)
        return matches


class GoalScorer(models.Model):
    footballer = models.ForeignKey(Footballer, on_delete=models.CASCADE, related_name='footballer_goals')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_goal_scorers')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('footballer',)

    def __str__(self):
        return self.footballer.name

    def clean(self):
        if self.footballer.team != self.match.home_team and self.footballer.team != self.match.away_team:
            raise ValidationError({"footballer": "This footballer didn't play in this match!"})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for bet in ExtraBets.objects.filter(footballer=self.footballer):
            bet.save()


class Bet(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='bets')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets_placed')
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    points = models.PositiveIntegerField(null=True, blank=True, default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('match', 'player')
        ordering = ('match__date_and_time', 'player', 'updated',)

    def __str__(self):
        result = f'{self.player.email} ({self.match.display_match()}, {self.display_bet()})'
        return result

    def display_bet(self):
        if self.home_score is None or self.away_score is None:
            return f'-'
        else:
            return f'{str(self.home_score)} : {str(self.away_score)}'

    @property
    def is_editable(self):
        return self.match.available_for_betting

    def save(self, *args, **kwargs):
        if self.match.home_score is not None or self.match.away_score is not None:
            match_goal_diff = self.match.home_score - self.match.away_score
            bet_goal_diff = self.home_score - self.away_score

            if self.match.home_score == self.home_score and self.match.away_score == self.away_score:
                self.points = ScoringSystem.objects.get(evaluated_field=self.match.tournament_stage).result_hitted

            elif match_goal_diff == bet_goal_diff:
                self.points = ScoringSystem.objects.get(evaluated_field=self.match.tournament_stage).goal_diff_hitted

            elif (self.match.home_score > self.match.away_score and self.home_score > self.away_score) or \
                 (self.match.home_score < self.match.away_score and self.home_score < self.away_score) or \
                 (self.match.home_score == self.match.away_score and self.home_score == self.away_score):
                self.points = ScoringSystem.objects.get(evaluated_field=self.match.tournament_stage).direction_hitted

            else:
                self.points = 0

        super().save(*args, **kwargs)


class ExtraBets(models.Model):
    footballer = models.ForeignKey(Footballer, on_delete=models.CASCADE, related_name='footballer_extra_bets')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_extra_bets')
    player = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, related_name='player_extra_bets')
    points = models.PositiveIntegerField(null=True, blank=True, default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('player', 'footballer')
        verbose_name_plural = 'Extra Bets'

    def __str__(self):
        return f'{self.player.email}: {self.footballer.name} / {self.team.name}'

    @property
    def is_editable(self):
        return timezone.now() < Match.objects.earliest('date_and_time').date_and_time

    def save(self, *args, **kwargs):
        footballer_goals = GoalScorer.objects.filter(footballer=self.footballer).count()
        points_for_goals = footballer_goals * ScoringSystem.objects.get(evaluated_field='Goal').other_points

        is_top_scorer = Footballer.objects.get(id=self.footballer.id).is_top_scorer
        if is_top_scorer:
            points_for_top_scorer = ScoringSystem.objects.get(evaluated_field='Top Scorer').other_points
        else:
            points_for_top_scorer = 0

        is_champion = Team.objects.get(id=self.team.id).is_champion
        if is_champion:
            points_for_champion = ScoringSystem.objects.get(evaluated_field='World Champion').other_points
        else:
            points_for_champion = 0

        self.points = points_for_goals + points_for_top_scorer + points_for_champion
        super().save(*args, **kwargs)


class InfoText(models.Model):
    title = models.CharField(max_length=200, unique=True, blank=False)
    slug = models.SlugField(unique=True)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title}'

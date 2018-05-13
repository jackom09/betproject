from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.forms import formset_factory
from .models import User, Match, Bet, ExtraBets, InfoText
from .forms import UserRegistrationForm, UserEditForm, BetForm, ExtraBetsForm


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            return render(request,
                          'betapp/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request,
                  'betapp/register.html',
                  {'user_form': user_form})


@login_required
def settings(request):
    return render(request,
                  'betapp/settings.html')


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        if user_form.is_valid():
            user_form.save()
            return redirect('settings')
    else:
        user_form = UserEditForm(instance=request.user)
    return render(request,
                  'betapp/edit.html',
                  {'user_form': user_form})


@login_required
def index_view(request):
    std_points = {}
    ext_points = {}

    if Bet.objects.filter(player=request.user).exists():
        std_points = Bet.objects.filter(player=request.user).aggregate(Sum('points'))
    else:
        std_points['points__sum'] = 0

    if ExtraBets.objects.filter(player=request.user).exists():
        ext_points = ExtraBets.objects.filter(player=request.user).aggregate(Sum('points'))
    else:
        ext_points['points__sum'] = 0

    total_points = std_points['points__sum'] + ext_points['points__sum']

    return render(request, 'betapp/index.html', {'points': total_points})


class MatchListView(LoginRequiredMixin, ListView):
    model = Match
    template_name = 'betapp/match_list.html'
    context_object_name = 'matches'
    paginate_by = 15

    @staticmethod
    def bets():
        return Bet.objects.all()


@login_required
def bet_form_view(request, pk):
    match = get_object_or_404(Match.available_bet_list(), pk=pk)

    if Bet.objects.filter(match=match, player=request.user).exists():
        bet = Bet.objects.get(match=match, player=request.user)
    else:
        bet = Bet(match=match, player=request.user)

    form = BetForm(request.POST or None, instance=bet)
    if form.is_valid():
        form.save()
        return redirect('match_list')

    return render(request, 'betapp/bet_form.html', {'form': form,
                                                    'match': match})


@login_required
def bet_formset_view(request):
    matches = Match.available_bet_list()
    BetFormSet = formset_factory(form=BetForm, extra=len(matches), max_num=len(matches))

    formset = BetFormSet(request.POST or None)
    if formset.is_valid():
        for match_count in range(len(matches)):
            if Bet.objects.filter(player=request.user, match=matches[match_count]).exists():
                bet = Bet.objects.get(player=request.user, match=matches[match_count])
            else:
                bet = Bet()
                bet.player = request.user
                bet.match = matches[match_count]
            if request.POST[f'form-{match_count}-home_score'] and request.POST[f'form-{match_count}-away_score']:
                bet.home_score = request.POST[f'form-{match_count}-home_score']
                bet.away_score = request.POST[f'form-{match_count}-away_score']
                bet.save()
        return redirect('match_list')

    bets = Bet.objects.all()
    match_formset_zip = zip(matches, formset)
    return render(request, 'betapp/bet_formset.html', {'matches': matches,
                                                       'formset': formset,
                                                       'match_formset_zip': match_formset_zip,
                                                       'bets': bets})


@login_required
def extra_bets_form_view(request):
    if ExtraBets.objects.filter(player=request.user).exists():
        extra_bets = ExtraBets.objects.get(player=request.user)
    else:
        extra_bets = ExtraBets(player=request.user)

    extra_bets_form = ExtraBetsForm(request.POST or None, instance=extra_bets)
    if extra_bets_form.is_valid():
        extra_bets_form.save()
        return redirect('index')

    return render(request, 'betapp/extra_bets_form.html', {'extra_bets_form': extra_bets_form,
                                                           'extra_bets': extra_bets})


@login_required
def players_table_view(request):
    users = User.objects.all()
    players_list = []
    std_points = {}
    ext_points = {}

    for user in users:
        if Bet.objects.filter(player=user).exists():
            std_points = Bet.objects.filter(player=user).aggregate(Sum('points'))
        else:
            std_points['points__sum'] = 0

        if ExtraBets.objects.filter(player=user).exists():
            ext_points = ExtraBets.objects.filter(player=user).aggregate(Sum('points'))
        else:
            ext_points['points__sum'] = 0

        total_points = std_points['points__sum'] + ext_points['points__sum']

        player = {'player': user,
                  'standard_points': std_points['points__sum'],
                  'extra_points': ext_points['points__sum'],
                  'total_points': total_points}

        players_list.append(player)

    return render(request, 'betapp/players_table.html', {'players_list': players_list})


class AllBetsListView(LoginRequiredMixin, ListView):
    # queryset = Bet.objects.filter(match__date_and_time__lte=timezone.now()).order_by('match__date_and_time')
    model = User
    context_object_name = 'players'
    template_name = 'betapp/all_bets.html'

    @staticmethod
    def bets():
        return Bet.objects.filter(match__date_and_time__lte=timezone.now()).order_by('match__date_and_time')

    @staticmethod
    def matches():
        return Match.objects.filter(date_and_time__lte=timezone.now())

    # @staticmethod
    # def players():
    #     return User.objects.all()

    @staticmethod
    def extra_bets():
        return ExtraBets.objects.all()


@login_required
def info_license(request):
    license = get_object_or_404(InfoText, slug='license')
    return render(request, 'betapp/infos/license.html', {'license': license})


@login_required
def info_terms(request):
    terms = get_object_or_404(InfoText, slug='terms-use')
    return render(request, 'betapp/infos/terms.html', {'terms': terms})

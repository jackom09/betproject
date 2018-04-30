from django import forms
from .models import User, Bet, ExtraBets


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Incorrect password repetition.')
        return cd['password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class BetForm(forms.ModelForm):
    class Meta:
        model = Bet
        fields = ('home_score', 'away_score')
        widgets = {
            'home_score': forms.TextInput(attrs={'size': '1', 'style': 'text-align: center'}),
            'away_score': forms.TextInput(attrs={'size': '1', 'style': 'text-align: center'}),
        }


class ExtraBetsForm(forms.ModelForm):
    class Meta:
        model = ExtraBets
        fields = ('footballer', 'team')

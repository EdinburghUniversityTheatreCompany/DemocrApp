from django import forms
from Meeting.models import Vote


class VoteForm(forms.Form):
    name = forms.CharField(label='Name', max_length=150)
    description = forms.CharField(label="Description", widget=forms.Textarea, required=False)
    method = forms.ChoiceField(label="Method", choices=Vote.methods)
    majority_threshold = forms.ChoiceField(
        label="Majority Threshold",
        choices=[
            ('', '-- please select --'),
            ('simple', 'Simple Majority'),
            ('two_thirds', 'Two-Thirds Majority'),
        ],
        required=False,
        help_text="For YNA votes: determines pass/fail"
    )
    num_seats = forms.IntegerField(
        label="Number of Seats",
        required=False,
        min_value=1,
        help_text="For STV votes: number of positions to elect"
    )

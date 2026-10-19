from django import forms
from .models import Comment, ContactMessage
class HoneypotMixin(forms.Form):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    def clean_website(self):
        if self.cleaned_data.get('website'): raise forms.ValidationError('Unable to accept this submission.')
        return ''
class CommentForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name','body']
        widgets = {'body': forms.Textarea(attrs={'rows':4})}
        labels = {'body':'Your comment'}
class ContactForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name','email','message']
        widgets = {'message': forms.Textarea(attrs={'rows':6})}

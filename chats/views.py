from django.views.generic import TemplateView

from chats.models import Conversation


class ChatView(TemplateView):
    template_name = 'chats/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_id = self.kwargs.get('document_id')

        conversation = Conversation.objects.filter(document_id=document_id)
        context['conversation'] = conversation
        context['document_id'] = document_id
        return context
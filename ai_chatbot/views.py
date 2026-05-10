from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .models import ChatSession, ChatMessage
from .services import AIChatbotService

def get_session(user):
    session = ChatSession.objects.filter(student=user, is_active=True).first()
    if not session:
        session = ChatSession.objects.create(student=user)
        ChatMessage.objects.create(
            session=session, 
            message_type='bot', 
            content="👋 Hi! I'm your AI Study Assistant. Ask me anything about your courses, assignments, or study tips!"
        )
    return session

@login_required
def chat_widget(request):
    session = get_session(request.user)
    return render(request, 'ai_chatbot/widget.html', {'messages': session.messages.all()})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_message_ajax(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        session = get_session(request.user)
        
        # Save user message
        ChatMessage.objects.create(session=session, message_type='user', content=user_message)
        
        # Get AI response
        ai_service = AIChatbotService(request.user)
        ai_response = ai_service.get_response(user_message)
        
        # Save bot response
        ChatMessage.objects.create(session=session, message_type='bot', content=ai_response)
        
        session.last_active = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'time': timezone.now().strftime('%I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': True,
            'response': f"😅 Error: {str(e)[:100]}",
            'time': timezone.now().strftime('%I:%M %p')
        })

@login_required
def get_messages(request):
    session = ChatSession.objects.filter(student=request.user, is_active=True).first()
    if not session:
        return JsonResponse({'messages': []})
    
    return JsonResponse({
        'messages': [
            {
                'type': msg.message_type,
                'content': msg.content,
                'time': msg.created_at.strftime('%I:%M %p')
            }
            for msg in session.messages.all()
        ]
    })

@login_required
def clear_chat_ajax(request):
    if request.method == 'POST':
        ChatSession.objects.filter(student=request.user, is_active=True).update(is_active=False)
        new_session = ChatSession.objects.create(student=request.user)
        ChatMessage.objects.create(
            session=new_session,
            message_type='bot',
            content="👋 New conversation started! How can I help you today?"
        )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)
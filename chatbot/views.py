import uuid
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import ChatSession, ChatMessage
from .services import ChatbotService

class ChatbotView(View):
    def get(self, request):
        """Render the chatbot interface with optional session_id"""
        session_id = request.GET.get('session_id')

        # If no session_id provided, create a new one
        if not session_id:
            session_id = str(uuid.uuid4())
            ChatSession.objects.create(session_id=session_id)

        context = {
            'initial_session_id': session_id
        }
        return render(request, 'chatbot/index.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    def __init__(self):
        super().__init__()
        self.chatbot_service = ChatbotService()

    def post(self, request):
        """Handle chat messages - store only human messages and final AI responses"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            session_id = data.get('session_id')

            if not message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Get or create session
            session, created = ChatSession.objects.get_or_create(
                session_id=session_id if session_id else str(uuid.uuid4())
            )

            # Store the human message
            ChatMessage.objects.create(
                session=session,
                message_type='human',
                content=message
            )

            # Get conversation history (only human and ai messages, no tool messages)
            previous_messages = ChatMessage.objects.filter(
                session=session,
                message_type__in=['human', 'ai']  # Only get human and AI messages
            ).order_by('timestamp')

            # Build conversation history for LangGraph (simple format)
            conversation_history = []
            for msg in previous_messages:
                conversation_history.append({
                    'type': msg.message_type,
                    'content': msg.content
                })

            # Process the message through LangGraph
            response_messages = self.chatbot_service.process_message(
                message,
                conversation_history
            )

            # Extract only the final AI response from all the response messages
            final_ai_response = ""
            for resp_msg in response_messages:
                if resp_msg['type'] == 'ai' and resp_msg['content']:
                    final_ai_response = resp_msg['content']

            # Store only the final AI response (ignore all tool messages)
            if final_ai_response:
                ChatMessage.objects.create(
                    session=session,
                    message_type='ai',
                    content=final_ai_response,
                    tool_calls=[],  # Empty list since we're not storing tool calls
                    tool_call_id=None
                )
            else:
                # Fallback if no AI response found
                final_ai_response = "I apologize, but I couldn't process your request at the moment."
                ChatMessage.objects.create(
                    session=session,
                    message_type='ai',
                    content=final_ai_response,
                    tool_calls=[],
                    tool_call_id=None
                )

            return JsonResponse({
                'response': final_ai_response,
                'session_id': session.session_id,
                'status': 'success'
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class ChatHistoryView(View):
    def get(self, request, session_id):
        """Get chat history for a session (only human and AI messages)"""
        try:
            session = ChatSession.objects.get(session_id=session_id)
            # Only get human and AI messages, exclude tool messages
            messages = ChatMessage.objects.filter(
                session=session,
                message_type__in=['human', 'ai']
            ).order_by('timestamp')

            history = []
            for msg in messages:
                history.append({
                    'type': msg.message_type,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat()
                    # Removed tool_calls from history since we're not using them
                })

            return JsonResponse({
                'history': history,
                'session_id': session_id
            })

        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def test_tools(request):
    """Test endpoint to verify tools are working"""
    if request.method == 'POST':
        try:
            chatbot_service = ChatbotService()

            # Test with a simple query
            test_messages = chatbot_service.process_message("What is 1706.03762 about?")

            # Extract only the final AI response for testing
            final_response = ""
            for msg in test_messages:
                if msg['type'] == 'ai' and msg['content']:
                    final_response = msg['content']

            return JsonResponse({
                'final_response': final_response,
                'status': 'success'
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)
import requests
import json
import random
from django.conf import settings
from django.utils import timezone
from courses.models import Course
from assignments.models import Assignment, Submission

class AIChatbotService:
    def __init__(self, user):
        self.user = user
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
    
    def get_response(self, user_message):
        # Try Gemini API first
        response = self.call_gemini_api(user_message)
        if response:
            return response
        
        # Fallback to smart responses
        return self.get_smart_response(user_message)
    
    def call_gemini_api(self, user_message):
        """Call Google Gemini API with correct endpoint"""
        if not self.api_key or len(self.api_key) < 10:
            return None
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
            context = self.get_user_context()
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"""{context}

You are a helpful, friendly AI Study Assistant for IUB LMS. 

Rules:
- Be warm and encouraging
- Never give direct answers to assignments - provide helpful hints and guidance
- Keep responses concise (under 100 words)
- Focus on helping students learn

Student question: {user_message}

Your helpful response:"""
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 300
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    return data['candidates'][0]['content']['parts'][0]['text']
            return None
                
        except Exception as e:
            print(f"Gemini API Exception: {e}")
            return None
    
    def get_user_context(self):
        """Get user-specific context for personalized responses"""
        context = f"Student Name: {self.user.get_full_name() or self.user.username}\nRole: {self.user.get_role_display()}\n"
        
        if self.user.role == 'student':
            courses = self.user.enrolled_courses.all()
            if courses:
                course_list = ", ".join([f"{c.title}" for c in courses])
                context += f"Enrolled Courses: {course_list}\n"
            
            # Get pending assignments count
            assignments = Assignment.objects.filter(course__in=courses)
            submissions = Submission.objects.filter(student=self.user)
            submitted_ids = submissions.values_list('assignment_id', flat=True)
            pending = assignments.exclude(id__in=submitted_ids).filter(deadline__gt=timezone.now())
            if pending:
                pending_list = ", ".join([a.title for a in pending[:3]])
                context += f"Pending Assignments: {pending_list}\n"
        
        context += f"\nCurrent Time: {timezone.now().strftime('%I:%M %p, %b %d, %Y')}\n"
        return context
    
    def get_smart_response(self, user_message):
        """Fallback smart responses when API fails"""
        msg = user_message.lower().strip()
        
        # Help menu
        if msg in ['help', 'commands', 'menu']:
            return self.get_help_menu()
        
        # Greetings
        if any(w in msg for w in ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'salam']):
            return self.get_greeting()
        
        # Courses
        if any(w in msg for w in ['course', 'courses', 'enrolled', 'subjects', 'my courses']):
            return self.get_courses_info()
        
        # Assignments
        if any(w in msg for w in ['assignment', 'assignments', 'pending', 'homework', 'task', 'work']):
            return self.get_assignments_info()
        
        # Deadlines
        if any(w in msg for w in ['deadline', 'due', 'upcoming', 'submission', 'dates']):
            return self.get_deadlines_info()
        
        # Study Tips
        if any(w in msg for w in ['tip', 'tips', 'study', 'learn', 'how to study', 'advice']):
            return self.get_study_tips()
        
        # Attendance
        if any(w in msg for w in ['attendance', 'present', 'absent', 'lecture', 'class']):
            return self.get_attendance_info()
        
        # Grades/Performance
        if any(w in msg for w in ['grade', 'marks', 'performance', 'score', 'result', 'cgpa']):
            return self.get_performance_info()
        
        # About bot
        if any(w in msg for w in ['who are you', 'what are you', 'about', 'yourself']):
            return self.get_about_info()
        
        # Thanks
        if any(w in msg for w in ['thanks', 'thank you', 'thx', 'appreciate']):
            return self.get_thanks_response()
        
        # Goodbye
        if any(w in msg for w in ['bye', 'goodbye', 'see you', 'later']):
            return self.get_goodbye_response()
        
        # Default
        return self.get_default_response()
    
    # ============================================================
    # RESPONSE METHODS - CLEAN VERSION (NO STARS)
    # ============================================================
    
    def get_help_menu(self):
        return """[ AI Assistant Commands ]

Here's what I can help you with:

[1] my courses - Show your enrolled courses
[2] pending assignments - List homework that needs submission
[3] deadlines - Show upcoming due dates
[4] study tips - Get learning advice and techniques
[5] attendance - View your lecture attendance
[6] performance - Check your grades and scores
[7] help - Show this menu

Just type any command!

Example: "my courses" or "pending assignments"
"""
    
    def get_greeting(self):
        hour = timezone.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        name = self.user.get_full_name() or self.user.username
        
        return f"""{greeting}, {name}!

I am your AI Study Assistant for IUB LMS.

Quick commands:
- Type "help" to see everything I can do
- Type "my courses" to see your enrolled courses
- Type "pending assignments" to check homework

How can I help you today?
"""
    
    def get_courses_info(self):
        courses = self.user.enrolled_courses.all()
        
        if not courses:
            return """[ No Courses Enrolled ]

You are not enrolled in any courses yet.

What to do:
1. Contact your course administrator
2. Ask your teacher to enroll you
3. Check course registration portal

Need help with anything else?
"""
        
        response = f"[ Your Enrolled Courses ] - Total: {courses.count()}\n\n"
        
        for i, course in enumerate(courses, 1):
            students_count = course.students.count()
            assignments_count = course.assignments.count()
            
            response += f"{i}. {course.title}\n"
            response += f"   Code: {course.course_code}\n"
            response += f"   Teacher: {course.teacher.get_full_name() or course.teacher.username if course.teacher else 'Not assigned'}\n"
            response += f"   Students: {students_count}\n"
            response += f"   Assignments: {assignments_count}\n\n"
        
        response += "Need help with a specific course? Just ask!"
        return response
    
    def get_assignments_info(self):
        courses = self.user.enrolled_courses.all()
        
        if not courses:
            return "You are not enrolled in any courses, so there are no assignments."
        
        assignments = Assignment.objects.filter(course__in=courses)
        submissions = Submission.objects.filter(student=self.user)
        submitted_ids = submissions.values_list('assignment_id', flat=True)
        pending = assignments.exclude(id__in=submitted_ids).filter(deadline__gt=timezone.now())
        
        if pending.exists():
            response = f"[ Pending Assignments ] - {pending.count()} pending\n\n"
            
            for assignment in pending:
                days_left = (assignment.deadline - timezone.now()).days
                
                if days_left <= 2:
                    priority = "URGENT"
                elif days_left <= 5:
                    priority = "SOON"
                else:
                    priority = "NORMAL"
                
                response += f"Assignment: {assignment.title}\n"
                response += f"   Course: {assignment.course.title}\n"
                response += f"   Due: {assignment.deadline.strftime('%b %d, %Y at %I:%M %p')}\n"
                response += f"   Days Left: {days_left}\n"
                response += f"   Priority: {priority}\n"
                response += f"   Max Marks: {assignment.max_marks}\n\n"
            
            response += "Tip: Start with urgent assignments first!"
            return response
        else:
            submitted_count = submissions.count()
            if submitted_count > 0:
                return f"Great job! You have no pending assignments. You have submitted {submitted_count} assignment(s). Keep up the excellent work!"
            else:
                return "No pending assignments found. This is a good time to review past materials or prepare for upcoming tasks."
    
    def get_deadlines_info(self):
        courses = self.user.enrolled_courses.all()
        
        if not courses:
            return "You are not enrolled in any courses."
        
        assignments = Assignment.objects.filter(course__in=courses, deadline__gt=timezone.now()).order_by('deadline')[:10]
        
        if assignments.exists():
            response = f"[ Upcoming Deadlines ] - Next {assignments.count()} tasks\n\n"
            
            for assignment in assignments:
                days_left = (assignment.deadline - timezone.now()).days
                response += f"Assignment: {assignment.title}\n"
                response += f"   Course: {assignment.course.title}\n"
                response += f"   Due: {assignment.deadline.strftime('%b %d, %Y at %I:%M %p')}\n"
                response += f"   Days remaining: {days_left}\n\n"
            
            return response
        else:
            return "No upcoming deadlines. Great time management!"
    
    def get_study_tips(self):
        tips = [
            "Create a schedule - Set specific times for each subject and stick to your routine.",
            "Break it down - Divide large tasks into smaller, manageable chunks.",
            "Pomodoro Technique - Study 25 minutes, take 5 minutes break. Repeat 4 times, then take longer break.",
            "Active learning - Take notes, create summaries, and teach what you learn to others.",
            "Get enough sleep - 7-8 hours of sleep improves memory and concentration.",
            "Take breaks - Short walks or stretches refresh your mind.",
            "Review regularly - Review notes within 24 hours, then weekly.",
            "Set goals - Have clear, achievable goals for each study session.",
            "Remove distractions - Keep your phone away while studying.",
            "Stay hydrated - Drink water regularly to maintain focus."
        ]
        
        selected_tips = random.sample(tips, 3)
        
        response = "[ Study Tips for Success ]\n\n"
        for tip in selected_tips:
            response += f"- {tip}\n\n"
        
        response += "Would you like more tips? Type 'study tips' again!"
        return response
    
    def get_attendance_info(self):
        try:
            from courses.models import Lecture, LectureAttendance
            
            courses = self.user.enrolled_courses.all()
            
            if not courses:
                return "You are not enrolled in any courses."
            
            lectures = Lecture.objects.filter(course__in=courses, is_published=True)
            total_lectures = lectures.count()
            attended_lectures = LectureAttendance.objects.filter(student=self.user, lecture__in=lectures).count()
            
            if total_lectures == 0:
                return "No lectures available yet. Check back later for video lectures!"
            
            percentage = (attended_lectures / total_lectures) * 100
            
            if percentage >= 75:
                status = "Excellent"
                message = "Keep up the great work!"
            elif percentage >= 60:
                status = "Good"
                message = "Try to attend a few more lectures to reach 75 percent."
            elif percentage >= 40:
                status = "Average"
                message = "Your attendance needs improvement."
            else:
                status = "Low"
                message = "Please attend more lectures regularly to stay on track."
            
            response = f"[ Attendance Report ]\n\n"
            response += f"Overall: {attended_lectures} out of {total_lectures} lectures ({percentage:.1f}%)\n"
            response += f"Status: {status}\n\n"
            response += message + "\n"
            
            return response
            
        except ImportError:
            return "Attendance feature is being set up. Check back soon!"
    
    def get_performance_info(self):
        submissions = Submission.objects.filter(student=self.user, marks__isnull=False)
        
        if not submissions.exists():
            return """[ No Grades Available Yet ]

You haven't received any grades so far.

What to do:
1. Complete pending assignments
2. Submit work before deadlines
3. Check back after teachers grade your work

Keep working hard!
"""
        
        total_obtained = sum(s.marks for s in submissions)
        total_max = sum(s.assignment.max_marks for s in submissions)
        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        
        if percentage >= 80:
            grade = "A" 
            remark = "Excellent! Outstanding performance!"
        elif percentage >= 70:
            grade = "B"
            remark = "Good! Well done!"
        elif percentage >= 60:
            grade = "C"
            remark = "Satisfactory! Good effort."
        elif percentage >= 50:
            grade = "D"
            remark = "Needs improvement. Review your weak areas."
        else:
            grade = "F"
            remark = "Need to work harder. Focus on understanding concepts."
        
        response = f"[ Academic Performance Report ]\n\n"
        response += f"Overall Score: {total_obtained} out of {total_max} ({percentage:.1f}%)\n"
        response += f"Grade: {grade}\n"
        response += f"{remark}\n\n"
        
        # Recent graded assignments
        response += "Recent Graded Assignments:\n\n"
        for sub in submissions.order_by('-graded_at')[:5]:
            response += f"- {sub.assignment.title}\n"
            response += f"  Marks: {sub.marks} out of {sub.assignment.max_marks}\n"
            if sub.feedback:
                response += f"  Feedback: {sub.feedback[:80]}\n"
            response += "\n"
        
        if percentage < 60:
            response += """Improvement Tips:
- Review feedback on assignments
- Ask teachers for clarification
- Practice more problems
- Join study groups
"""
        
        return response
    
    def get_about_info(self):
        return """[ About Your AI Assistant ]

I am IUB LMS's AI Study Assistant, designed to help you succeed in your studies.

My Capabilities:
- Answer questions about your courses
- Track assignment deadlines
- Provide study tips and learning strategies
- Check attendance records
- Show grade reports
- Give hints without doing your work

My Goal: Help you learn better and stay organized!

Quick start: Type "help" to see all commands.

What would you like to know today?
"""
    
    def get_thanks_response(self):
        thanks_responses = [
            "You are welcome! Glad I could help.",
            "Anytime! Keep up the great work.",
            "Happy to help! Remember, consistency is key to success.",
            "You are welcome! Keep studying hard - you've got this.",
            "My pleasure! Stay focused and you will do great."
        ]
        return random.choice(thanks_responses)
    
    def get_goodbye_response(self):
        name = self.user.get_full_name() or self.user.username
        return f"""Goodbye, {name}!

Keep working hard and stay focused!

Remember to:
- Check deadlines regularly
- Complete assignments on time
- Take care of your health

Come back anytime you need help!
"""
    
    def get_default_response(self):
        return """I didn't quite understand that.

Try these commands:

- "my courses" - See enrolled courses
- "pending assignments" - Check homework
- "study tips" - Get learning advice
- "deadlines" - View due dates
- "attendance" - Check your record
- "performance" - See your grades
- "help" - Complete command list

What would you like to know?
"""
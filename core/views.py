from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import CustomUser
from courses.models import Course, Content, Announcement
from assignments.models import Assignment, Submission

def home(request):
    """Landing page for non-authenticated users"""
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    context = {}
    
    if request.user.role == 'admin':
        total_students = CustomUser.objects.filter(role='student').count()
        total_teachers = CustomUser.objects.filter(role='teacher').count()
        total_courses = Course.objects.count()
        total_assignments = Assignment.objects.count()
        
        context.update({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_courses': total_courses,
            'total_assignments': total_assignments,
            'recent_users': CustomUser.objects.all().order_by('-date_joined')[:5],
            'recent_courses': Course.objects.all().order_by('-created_at')[:5],
        })
    
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        assignments = Assignment.objects.filter(course__in=courses)
        pending_submissions = Submission.objects.filter(assignment__in=assignments, marks__isnull=True).count()
        
        context.update({
            'courses': courses,
            'courses_count': courses.count(),
            'assignments_count': assignments.count(),
            'pending_submissions': pending_submissions,
        })
    
    elif request.user.role == 'student':
        enrolled_courses = request.user.enrolled_courses.all()
        assignments = Assignment.objects.filter(course__in=enrolled_courses)
        submitted_assignments = Submission.objects.filter(student=request.user)
        submitted_ids = submitted_assignments.values_list('assignment_id', flat=True)
        pending_assignments_list = assignments.exclude(id__in=submitted_ids).filter(deadline__gt=timezone.now())
        
        graded_assignments = []
        for submission in submitted_assignments:
            if submission.marks is not None:
                graded_assignments.append({
                    'assignment': submission.assignment,
                    'marks': submission.marks,
                    'max_marks': submission.assignment.max_marks,
                    'feedback': submission.feedback,
                })
        
        context.update({
            'enrolled_courses': enrolled_courses,
            'courses_count': enrolled_courses.count(),
            'assignments_count': assignments.count(),
            'pending_assignments': pending_assignments_list.count(),
            'pending_assignments_list': pending_assignments_list,
            'submitted_assignments': submitted_assignments,
            'graded_assignments': graded_assignments,
            'total_submitted': submitted_assignments.count(),
        })
    
    return render(request, 'core/dashboard.html', context)

@login_required
def announcements_view(request):
    """View all announcements for the user"""
    if request.user.role == 'student':
        enrolled_courses = request.user.enrolled_courses.all()
        announcements = Announcement.objects.filter(course__in=enrolled_courses)
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        announcements = Announcement.objects.filter(course__in=courses)
    else:  # admin
        announcements = Announcement.objects.all()
    
    return render(request, 'core/all_announcements.html', {'announcements': announcements})
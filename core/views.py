from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import CustomUser
from courses.models import Course, Content, Announcement, Lecture, LectureAttendance, LiveClass
from assignments.models import Assignment, Submission

def home(request):
    """Landing page - shows IUB LMS welcome page"""
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    """Dashboard - Role-based dashboard with statistics"""
    context = {}
    context['now'] = timezone.now()
    
    if request.user.role == 'admin':
        context.update({
            'total_students': CustomUser.objects.filter(role='student').count(),
            'total_teachers': CustomUser.objects.filter(role='teacher').count(),
            'total_courses': Course.objects.count(),
            'total_assignments': Assignment.objects.count(),
            'recent_users': CustomUser.objects.all().order_by('-date_joined')[:5],
            'recent_courses': Course.objects.all().order_by('-created_at')[:5],
        })
    
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        assignments = Assignment.objects.filter(course__in=courses)
        context.update({
            'courses': courses,
            'courses_count': courses.count(),
            'assignments_count': assignments.count(),
            'pending_submissions': Submission.objects.filter(assignment__in=assignments, marks__isnull=True).count(),
        })
    
    elif request.user.role == 'student':
        # Student's Enrolled Courses
        enrolled_courses = request.user.enrolled_courses.all()
        courses_count = enrolled_courses.count()
        
        # All Assignments
        assignments = Assignment.objects.filter(course__in=enrolled_courses)
        assignments_count = assignments.count()
        
        # Student's Submissions
        submissions = Submission.objects.filter(student=request.user)
        submitted_assignments = submissions
        submitted_ids = submitted_assignments.values_list('assignment_id', flat=True)
        
        # Pending Assignments
        pending_assignments_list = assignments.exclude(
            id__in=submitted_ids
        ).filter(deadline__gt=timezone.now())
        pending_assignments = pending_assignments_list.count()
        
        # Overdue Assignments
        overdue_assignments = assignments.exclude(
            id__in=submitted_ids
        ).filter(deadline__lte=timezone.now()).count()
        
        # Graded Assignments
        graded_assignments = []
        total_obtained_marks = 0
        total_max_marks = 0
        
        for submission in submitted_assignments:
            if submission.marks is not None:
                percentage = (submission.marks / submission.assignment.max_marks) * 100 if submission.assignment.max_marks > 0 else 0
                graded_assignments.append({
                    'submission': submission,
                    'assignment': submission.assignment,
                    'marks': submission.marks,
                    'max_marks': submission.assignment.max_marks,
                    'percentage': round(percentage, 1),
                    'feedback': submission.feedback,
                })
                total_obtained_marks += submission.marks
                total_max_marks += submission.assignment.max_marks
        
        # Overall Performance
        overall_percentage = round((total_obtained_marks / total_max_marks * 100), 1) if total_max_marks > 0 else 0
        
        # ========== ATTENDANCE DATA - FIXED ==========
        lectures = Lecture.objects.filter(course__in=enrolled_courses, is_published=True)
        total_lectures = lectures.count()
        attended_lectures = LectureAttendance.objects.filter(
            student=request.user, 
            lecture__in=lectures
        ).count()
        attendance_percentage = round((attended_lectures / total_lectures) * 100, 1) if total_lectures > 0 else 0
        absent_lectures = total_lectures - attended_lectures
        
        # Course-wise Attendance
        course_attendance = []
        for course in enrolled_courses:
            course_lectures = Lecture.objects.filter(course=course, is_published=True)
            course_total = course_lectures.count()
            course_attended = LectureAttendance.objects.filter(
                student=request.user,
                lecture__in=course_lectures
            ).count()
            course_percentage = round((course_attended / course_total) * 100, 1) if course_total > 0 else 0
            
            course_attendance.append({
                'course': course,
                'attended': course_attended,
                'total': course_total,
                'percentage': course_percentage,
                'absent': course_total - course_attended,
            })
        
        context.update({
            'enrolled_courses': enrolled_courses,
            'courses_count': courses_count,
            'assignments_count': assignments_count,
            'pending_assignments': pending_assignments,
            'pending_assignments_list': pending_assignments_list,
            'overdue_assignments': overdue_assignments,
            'submitted_assignments': submitted_assignments,
            'total_submitted': submitted_assignments.count(),
            'graded_assignments': graded_assignments,
            'graded_count': len(graded_assignments),
            'total_obtained_marks': total_obtained_marks,
            'total_max_marks': total_max_marks,
            'overall_percentage': overall_percentage,
            # Attendance Data
            'attended_lectures': attended_lectures,
            'total_lectures': total_lectures,
            'attendance_percentage': attendance_percentage,
            'absent_lectures': absent_lectures,
            'course_attendance': course_attendance,
        })
    
    return render(request, 'core/dashboard.html', context)


@login_required
def announcements(request):
    """View all announcements across courses"""
    if request.user.role == 'student':
        enrolled_courses = request.user.enrolled_courses.all()
        announcements = Announcement.objects.filter(course__in=enrolled_courses)
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        announcements = Announcement.objects.filter(course__in=courses)
    else:
        announcements = Announcement.objects.all()
    
    return render(request, 'core/all_announcements.html', {'announcements': announcements})


@login_required
def all_lectures(request):
    """Show all video lectures from enrolled/assigned courses"""
    if request.user.role == 'student':
        enrolled_courses = request.user.enrolled_courses.all()
        lectures = Lecture.objects.filter(course__in=enrolled_courses, is_published=True)
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        lectures = Lecture.objects.filter(course__in=courses, is_published=True)
    else:
        lectures = Lecture.objects.filter(is_published=True)
    
    attended_lectures = []
    if request.user.role == 'student':
        attended_lectures = LectureAttendance.objects.filter(student=request.user).values_list('lecture_id', flat=True)
    
    watched_count = attended_lectures.count() if request.user.role == 'student' else 0
    total_lectures = lectures.count()
    progress_percentage = int((watched_count / total_lectures) * 100) if total_lectures > 0 else 0
    
    context = {
        'lectures': lectures,
        'attended_lectures': attended_lectures,
        'total_lectures': total_lectures,
        'watched_count': watched_count,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'courses/all_lectures.html', context)


@login_required
def live_class_list_all(request):
    """Show all live classes from enrolled/assigned courses"""
    if request.user.role == 'student':
        enrolled_courses = request.user.enrolled_courses.all()
        live_classes = LiveClass.objects.filter(course__in=enrolled_courses)
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
        live_classes = LiveClass.objects.filter(course__in=courses)
    else:
        live_classes = LiveClass.objects.all()
    
    now = timezone.now()
    for lc in live_classes:
        if now > lc.end_time:
            lc.status = 'completed'
        elif lc.start_time <= now <= lc.end_time:
            lc.status = 'ongoing'
        else:
            lc.status = 'scheduled'
        lc.save()
    
    context = {
        'live_classes': live_classes,
        'now': now,
    }
    return render(request, 'courses/live_class_list_all.html', context)


@login_required
def my_attendance(request):
    """Students can view their own detailed attendance"""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page!')
        return redirect('dashboard')
    
    enrolled_courses = request.user.enrolled_courses.all()
    lectures = Lecture.objects.filter(course__in=enrolled_courses, is_published=True)
    
    attendance_data = []
    for lecture in lectures:
        attendance = LectureAttendance.objects.filter(student=request.user, lecture=lecture).first()
        attendance_data.append({
            'lecture': lecture,
            'attended': attendance is not None,
            'watched_at': attendance.watched_at if attendance else None,
        })
    
    total_lectures = lectures.count()
    attended_count = sum(1 for a in attendance_data if a['attended'])
    percentage = round((attended_count / total_lectures) * 100, 1) if total_lectures > 0 else 0
    
    context = {
        'attendance_data': attendance_data,
        'total_lectures': total_lectures,
        'attended_count': attended_count,
        'percentage': percentage,
    }
    return render(request, 'courses/my_attendance.html', context)
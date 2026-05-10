from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from datetime import datetime
from .models import Course, Content, Announcement, Lecture, LectureAttendance, LiveClass, LiveClassAttendance
from accounts.models import CustomUser
from assignments.models import Assignment, Submission

def is_admin(user):
    return user.role == 'admin'

def is_teacher(user):
    return user.role == 'teacher' or user.role == 'admin'


# ========== COURSE VIEWS ==========

@login_required
def course_list(request):
    if request.user.role == 'admin':
        courses = Course.objects.all()
    elif request.user.role == 'teacher':
        courses = Course.objects.filter(teacher=request.user)
    else:
        courses = request.user.enrolled_courses.all()
    return render(request, 'courses/course_list.html', {'courses': courses})


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('course_list')
    
    contents = course.contents.all()
    assignments = Assignment.objects.filter(course=course)
    lectures = Lecture.objects.filter(course=course, is_published=True)
    live_classes = LiveClass.objects.filter(course=course)
    announcements = Announcement.objects.filter(course=course)[:5]
    
    submissions = None
    if request.user.role == 'student':
        submissions = Submission.objects.filter(student=request.user, assignment__in=assignments)
    
    context = {
        'course': course,
        'contents': contents,
        'assignments': assignments,
        'lectures': lectures,
        'live_classes': live_classes,
        'announcements': announcements,
        'submissions': submissions,
    }
    return render(request, 'courses/course_detail.html', context)


@user_passes_test(is_admin)
def create_course(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course_code = request.POST.get('course_code')
        title = request.POST.get('title')
        description = request.POST.get('description')
        teacher_id = request.POST.get('teacher')
        
        teacher = None
        if teacher_id:
            try:
                teacher = CustomUser.objects.get(id=teacher_id)
            except:
                pass
        
        course = Course.objects.create(
            course_id=course_id,
            course_code=course_code,
            title=title,
            description=description,
            teacher=teacher
        )
        messages.success(request, f'Course "{title}" created!')
        return redirect('course_detail', course_id=course.id)
    
    teachers = CustomUser.objects.filter(role='teacher')
    return render(request, 'courses/create_course.html', {'teachers': teachers})


@user_passes_test(is_admin)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course_title = course.title
    course.delete()
    messages.success(request, f'Course "{course_title}" deleted!')
    return redirect('course_list')


# ========== CONTENT VIEWS ==========

@user_passes_test(is_teacher)
def upload_content(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content_type = request.POST.get('content_type')
        file = request.FILES.get('file')
        link_url = request.POST.get('link_url')
        text_content = request.POST.get('text_content')
        
        Content.objects.create(
            course=course,
            title=title,
            content_type=content_type,
            file=file,
            link_url=link_url,
            text_content=text_content,
            uploaded_by=request.user
        )
        messages.success(request, 'Content uploaded!')
        return redirect('course_detail', course_id=course.id)
    
    return render(request, 'courses/upload_content.html', {'course': course})


@user_passes_test(is_teacher)
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    course_id = content.course.id
    
    if request.user.role == 'admin' or content.uploaded_by == request.user:
        content.delete()
        messages.success(request, 'Content deleted!')
    else:
        messages.error(request, 'Not authorized!')
    
    return redirect('course_detail', course_id=course_id)


# ========== ENROLLMENT VIEWS ==========

@user_passes_test(is_admin)
def enroll_student(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        if student_id:
            try:
                student = CustomUser.objects.get(id=student_id, role='student')
                if student in course.students.all():
                    messages.warning(request, f'{student.username} already enrolled!')
                else:
                    course.students.add(student)
                    messages.success(request, f'{student.username} enrolled!')
            except:
                messages.error(request, 'Student not found!')
        else:
            messages.error(request, 'Select a student!')
        return redirect('course_detail', course_id=course.id)
    
    all_students = CustomUser.objects.filter(role='student')
    enrolled_students = course.students.all()
    available_students = all_students.exclude(id__in=enrolled_students)
    
    context = {
        'course': course,
        'students': available_students,
        'enrolled_students': enrolled_students,
    }
    return render(request, 'courses/enroll_student.html', context)


@user_passes_test(is_admin)
def remove_student(request, course_id, student_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    course.students.remove(student)
    messages.success(request, f'{student.username} removed!')
    return redirect('course_detail', course_id=course_id)


@user_passes_test(is_admin)
def manage_students(request):
    students = CustomUser.objects.filter(role='student')
    return render(request, 'courses/manage_students.html', {'students': students})


@user_passes_test(is_admin)
def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    student_name = student.username
    student.delete()
    messages.success(request, f'Student "{student_name}" deleted!')
    return redirect('manage_students')


# ========== ANNOUNCEMENT VIEWS ==========

@user_passes_test(is_teacher)
def create_announcement(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        attachment = request.FILES.get('attachment')
        
        Announcement.objects.create(
            course=course,
            title=title,
            content=content,
            priority=priority,
            attachment=attachment,
            created_by=request.user
        )
        messages.success(request, f'Announcement "{title}" posted!')
        return redirect('course_announcements', course_id=course.id)
    
    return render(request, 'courses/create_announcement.html', {'course': course})


@login_required
def course_announcements(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled!')
        return redirect('course_list')
    
    announcements = Announcement.objects.filter(course=course)
    return render(request, 'courses/course_announcements.html', {
        'course': course,
        'announcements': announcements
    })


@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    course_id = announcement.course.id
    
    if request.method == 'POST':
        if request.user.role == 'admin' or announcement.created_by == request.user:
            announcement.delete()
            messages.success(request, 'Announcement deleted!')
        else:
            messages.error(request, 'Not authorized!')
        return redirect('course_announcements', course_id=course_id)
    
    return redirect('course_announcements', course_id=course_id)


# ========== LECTURE VIEWS ==========

@login_required
def lecture_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled!')
        return redirect('course_list')
    
    lectures = Lecture.objects.filter(course=course, is_published=True)
    attended_lectures = []
    if request.user.role == 'student':
        attended_lectures = LectureAttendance.objects.filter(student=request.user, lecture__course=course).values_list('lecture_id', flat=True)
    
    context = {
        'course': course,
        'lectures': lectures,
        'attended_lectures': attended_lectures,
    }
    return render(request, 'courses/lecture_list.html', context)


@login_required
def lecture_detail(request, course_id, lecture_id):
    course = get_object_or_404(Course, id=course_id)
    lecture = get_object_or_404(Lecture, id=lecture_id, course=course)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled!')
        return redirect('course_list')
    
    if request.user.role == 'student':
        attendance, created = LectureAttendance.objects.get_or_create(
            student=request.user,
            lecture=lecture
        )
        if created:
            messages.success(request, 'Attendance marked!')
    
    attendance_count = LectureAttendance.objects.filter(lecture=lecture).count()
    
    context = {
        'course': course,
        'lecture': lecture,
        'attendance_count': attendance_count,
    }
    return render(request, 'courses/lecture_detail.html', context)


@user_passes_test(is_teacher)
def create_lecture(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_url = request.POST.get('video_url')
        duration = request.POST.get('duration')
        order = request.POST.get('order', 0)
        
        lecture = Lecture.objects.create(
            course=course,
            title=title,
            description=description,
            video_url=video_url,
            duration=duration,
            order=order,
            created_by=request.user
        )
        messages.success(request, f'Lecture "{title}" created!')
        return redirect('lecture_list', course_id=course.id)
    
    return render(request, 'courses/create_lecture.html', {'course': course})


@user_passes_test(is_teacher)
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course_id = lecture.course.id
    
    if request.user.role == 'admin' or lecture.created_by == request.user:
        lecture.delete()
        messages.success(request, 'Lecture deleted!')
    else:
        messages.error(request, 'Not authorized!')
    
    return redirect('lecture_list', course_id=course_id)


# ========== ATTENDANCE REPORT VIEWS (FIXED) ==========

@login_required
def lecture_attendance_report(request, course_id):
    """Teacher can see which students watched which video lectures"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Only teachers can view attendance!')
        return redirect('course_detail', course_id=course.id)
    
    lectures = Lecture.objects.filter(course=course, is_published=True)
    students = course.students.all()  # Get all enrolled students
    
    attendance_matrix = []
    for student in students:
        present_count = 0
        lecture_status = {}
        for lecture in lectures:
            attended = LectureAttendance.objects.filter(student=student, lecture=lecture).exists()
            lecture_status[lecture.id] = attended
            if attended:
                present_count += 1
        
        total = lectures.count()
        percentage = round((present_count / total) * 100, 1) if total > 0 else 0
        
        attendance_matrix.append({
            'student_name': student.get_full_name() or student.username,
            'student_username': student.username,
            'student_email': student.email,
            'present_count': present_count,
            'total_lectures': total,
            'percentage': percentage,
            'lecture_status': lecture_status,
        })
    
    context = {
        'course': course,
        'lectures': lectures,
        'attendance_matrix': attendance_matrix,
        'total_lectures': lectures.count(),
        'total_students': students.count(),
    }
    return render(request, 'courses/lecture_attendance_report.html', context)


@login_required
def live_class_attendance_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Only teachers can view attendance!')
        return redirect('course_detail', course_id=course.id)
    
    live_classes = LiveClass.objects.filter(course=course)
    
    context = {
        'course': course,
        'live_classes': live_classes,
    }
    return render(request, 'courses/live_class_attendance_list.html', context)


@login_required
def live_class_attendance_detail(request, course_id, live_class_id):
    course = get_object_or_404(Course, id=course_id)
    live_class = get_object_or_404(LiveClass, id=live_class_id)
    
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Only teachers can view attendance!')
        return redirect('course_detail', course_id=course.id)
    
    attendances = LiveClassAttendance.objects.filter(live_class=live_class)
    students = course.students.all()
    
    attendance_data = []
    for student in students:
        attendance = attendances.filter(student=student).first()
        attendance_data.append({
            'student_name': student.get_full_name() or student.username,
            'student_username': student.username,
            'student_email': student.email,
            'is_present': attendance is not None,
            'joined_at': attendance.joined_at if attendance else None,
        })
    
    context = {
        'course': course,
        'live_class': live_class,
        'attendance_data': attendance_data,
        'total_students': students.count(),
        'present_count': attendances.count(),
        'attendance_percentage': round((attendances.count() / students.count()) * 100, 1) if students.count() > 0 else 0,
    }
    return render(request, 'courses/live_class_attendance_detail.html', context)


# ========== LIVE CLASS VIEWS ==========

@login_required
def live_class_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled!')
        return redirect('course_list')
    
    live_classes = LiveClass.objects.filter(course=course)
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
        'course': course,
        'live_classes': live_classes,
        'now': now,
    }
    return render(request, 'courses/live_class_list.html', context)


@login_required
def live_class_list_all(request):
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
def create_live_class(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        
        if not start_time_str or not end_time_str:
            messages.error(request, 'Please select both start and end time!')
            return redirect('create_live_class', course_id=course.id)
        
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        start_time = timezone.make_aware(start_time)
        end_time = timezone.make_aware(end_time)
        
        meeting_link = str(uuid.uuid4())[:8]
        
        live_class = LiveClass.objects.create(
            course=course,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link,
            status='scheduled',
            created_by=request.user
        )
        messages.success(request, f'Live class "{title}" scheduled!')
        return redirect('live_class_list', course_id=course.id)
    
    return render(request, 'courses/create_live_class.html', {'course': course})


@login_required
def delete_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, id=live_class_id)
    course_id = live_class.course.id
    
    if request.user.role in ['admin', 'teacher']:
        live_class.delete()
        messages.success(request, 'Live class deleted!')
    else:
        messages.error(request, 'Not authorized!')
    
    return redirect('live_class_list', course_id=course_id)


@login_required
def start_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, id=live_class_id)
    now = timezone.now()
    
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Not authorized!')
        return redirect('live_class_list', course_id=live_class.course.id)
    
    if now < live_class.start_time:
        minutes_left = int((live_class.start_time - now).total_seconds() / 60)
        messages.error(request, f'Class starts in {minutes_left} minutes!')
        return redirect('live_class_list', course_id=live_class.course.id)
    
    if now > live_class.end_time:
        messages.error(request, 'Class has already ended!')
        return redirect('live_class_list', course_id=live_class.course.id)
    
    live_class.status = 'ongoing'
    live_class.save()
    messages.success(request, f'Live class "{live_class.title}" started!')
    return redirect('live_class_room', meeting_link=live_class.meeting_link)


@login_required
def live_class_room(request, meeting_link):
    live_class = get_object_or_404(LiveClass, meeting_link=meeting_link)
    course = live_class.course
    now = timezone.now()
    
    if now > live_class.end_time:
        messages.error(request, 'This live class has already ended! You cannot join.')
        return redirect('course_detail', course_id=course.id)
    
    if now < live_class.start_time:
        minutes_left = int((live_class.start_time - now).total_seconds() / 60)
        messages.error(request, f'Class starts in {minutes_left} minutes!')
        return redirect('course_detail', course_id=course.id)
    
    if request.user.role == 'student':
        if request.user not in course.students.all():
            messages.error(request, 'You are not enrolled!')
            return redirect('course_list')
    
    live_class.status = 'ongoing'
    live_class.save()
    
    if request.user.role == 'student':
        attendance, created = LiveClassAttendance.objects.get_or_create(
            live_class=live_class,
            student=request.user,
            defaults={'is_present': True}
        )
        if created:
            messages.success(request, 'Attendance marked!')
    
    context = {
        'live_class': live_class,
        'course': course,
        'is_teacher': request.user.role in ['admin', 'teacher'],
    }
    return render(request, 'courses/live_class_room.html', context)
@login_required
def test_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = course.students.all()
    
    context = {
        'course': course,
        'enrolled_students': students,
        'total_students': students.count(),
        'attendance_matrix': [],
    }
    return render(request, 'courses/test_attendance.html', context)
@login_required
def lecture_attendance_report(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role not in ['admin', 'teacher']:
        messages.error(request, 'Only teachers can view attendance!')
        return redirect('course_detail', course_id=course.id)
    
    lectures = Lecture.objects.filter(course=course, is_published=True)
    students = course.students.all()
    
    attendance_matrix = []
    total_attended = 0
    
    for student in students:
        present_count = 0
        lecture_status = {}
        for lecture in lectures:
            attended = LectureAttendance.objects.filter(student=student, lecture=lecture).exists()
            lecture_status[lecture.id] = attended
            if attended:
                present_count += 1
                total_attended += 1
        
        total = lectures.count()
        percentage = round((present_count / total) * 100, 1) if total > 0 else 0
        
        attendance_matrix.append({
            'student_name': student.get_full_name() or student.username,
            'student_username': student.username,
            'student_email': student.email,
            'present_count': present_count,
            'total_lectures': total,
            'percentage': percentage,
            'lecture_status': lecture_status,
        })
    
    total_possible = len(students) * len(lectures)
    overall_percentage = round((total_attended / total_possible) * 100, 1) if total_possible > 0 else 0
    
    context = {
        'course': course,
        'lectures': lectures,
        'attendance_matrix': attendance_matrix,
        'total_lectures': lectures.count(),
        'total_students': students.count(),
        'total_attended': total_attended,
        'overall_percentage': overall_percentage,
    }
    return render(request, 'courses/lecture_attendance_report.html', context)
@login_required
def my_attendance(request):
    """Students can view their own attendance only"""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page!')
        return redirect('dashboard')
    
    # Get all lectures from enrolled courses
    enrolled_courses = request.user.enrolled_courses.all()
    lectures = Lecture.objects.filter(course__in=enrolled_courses, is_published=True)
    
    # Get student's attendance
    attendance_data = []
    for lecture in lectures:
        attended = LectureAttendance.objects.filter(student=request.user, lecture=lecture).exists()
        attendance_data.append({
            'lecture': lecture,
            'attended': attended,
            'watched_at': LectureAttendance.objects.filter(student=request.user, lecture=lecture).first().watched_at if attended else None,
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
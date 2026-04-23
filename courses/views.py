from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Course, Content, Announcement
from accounts.models import CustomUser
from assignments.models import Assignment, Submission

def is_admin(user):
    return user.role == 'admin'

def is_teacher(user):
    return user.role == 'teacher' or user.role == 'admin'

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
    
    if request.user.role == 'student':
        if request.user not in course.students.all():
            messages.error(request, 'You are not enrolled in this course.')
            return redirect('course_list')
    
    contents = course.contents.all()
    assignments = Assignment.objects.filter(course=course)
    
    submissions = None
    if request.user.role == 'student':
        submissions = Submission.objects.filter(student=request.user, assignment__in=assignments)
    
    context = {
        'course': course,
        'contents': contents,
        'assignments': assignments,
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
        
        messages.success(request, f'Course "{title}" created successfully!')
        return redirect('course_detail', course_id=course.id)
    
    teachers = CustomUser.objects.filter(role='teacher')
    return render(request, 'courses/create_course.html', {'teachers': teachers})

# DELETE COURSE - NEW
@user_passes_test(is_admin)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course_title = course.title
    course.delete()
    messages.success(request, f'Course "{course_title}" deleted successfully!')
    return redirect('course_list')

@user_passes_test(is_teacher)
def upload_content(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher of this course!')
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
        
        messages.success(request, 'Content uploaded successfully!')
        return redirect('course_detail', course_id=course.id)
    
    return render(request, 'courses/upload_content.html', {'course': course})

# DELETE CONTENT - NEW
@user_passes_test(is_teacher)
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    course_id = content.course.id
    
    if request.user.role == 'admin' or content.uploaded_by == request.user:
        content.delete()
        messages.success(request, 'Content deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this content!')
    
    return redirect('course_detail', course_id=course_id)

@user_passes_test(is_admin)
def enroll_student(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        if student_id:
            try:
                student = CustomUser.objects.get(id=student_id, role='student')
                if student in course.students.all():
                    messages.warning(request, f'{student.username} is already enrolled!')
                else:
                    course.students.add(student)
                    messages.success(request, f'{student.username} has been enrolled!')
            except CustomUser.DoesNotExist:
                messages.error(request, 'Student not found!')
        else:
            messages.error(request, 'Please select a student!')
        
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
    messages.success(request, f'{student.username} has been removed from {course.title}!')
    
    return redirect('course_detail', course_id=course.id)

# DELETE STUDENT FROM SYSTEM - NEW (Admin only)
@user_passes_test(is_admin)
def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    student_name = student.username
    student.delete()
    messages.success(request, f'Student "{student_name}" has been deleted from system!')
    return redirect('manage_students')

# MANAGE STUDENTS - NEW (Admin only)
@user_passes_test(is_admin)
def manage_students(request):
    students = CustomUser.objects.filter(role='student')
    return render(request, 'courses/manage_students.html', {'students': students})

# ANNOUNCEMENT VIEWS
@login_required
def create_announcement(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student':
        messages.error(request, 'Students cannot create announcements!')
        return redirect('course_detail', course_id=course.id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher of this course!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        attachment = request.FILES.get('attachment')
        
        if not title or not content:
            messages.error(request, 'Title and content are required!')
            return redirect('create_announcement', course_id=course.id)
        
        Announcement.objects.create(
            course=course,
            title=title,
            content=content,
            priority=priority,
            attachment=attachment,
            created_by=request.user
        )
        
        messages.success(request, f'Announcement "{title}" posted successfully!')
        return redirect('course_announcements', course_id=course.id)
    
    return render(request, 'courses/create_announcement.html', {'course': course})

@login_required
def course_announcements(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'student' and request.user not in course.students.all():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('course_list')
    
    announcements = Announcement.objects.filter(course=course)
    
    context = {
        'course': course,
        'announcements': announcements,
    }
    return render(request, 'courses/course_announcements.html', context)

@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    course_id = announcement.course.id
    
    if request.user.role == 'admin' or announcement.created_by == request.user:
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this announcement!')
    
    return redirect('course_announcements', course_id=course_id)
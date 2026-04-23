from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Assignment, Submission
from courses.models import Course

def is_teacher(user):
    return user.role == 'teacher' or user.role == 'admin'

@login_required
def assignment_list(request):
    if request.user.role == 'admin':
        assignments = Assignment.objects.all()
    elif request.user.role == 'teacher':
        assignments = Assignment.objects.filter(course__teacher=request.user)
    else:
        assignments = Assignment.objects.filter(course__in=request.user.enrolled_courses.all())
    
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})

# CREATE ASSIGNMENT - FIXED
@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user.role == 'teacher' and course.teacher != request.user:
        messages.error(request, 'You are not the teacher of this course!')
        return redirect('course_detail', course_id=course.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        max_marks = request.POST.get('max_marks')
        attachment = request.FILES.get('attachment')  # This is correct now
        
        # Create assignment with attachment
        assignment = Assignment.objects.create(
            course=course,
            title=title,
            description=description,
            deadline=deadline,
            max_marks=max_marks,
            attachment=attachment,  # Now this works
            created_by=request.user
        )
        
        messages.success(request, f'Assignment "{title}" created successfully!')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    return render(request, 'assignments/create_assignment.html', {'course': course})

# DELETE ASSIGNMENT
@user_passes_test(is_teacher)
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course_id = assignment.course.id
    
    if request.user.role == 'admin' or assignment.created_by == request.user:
        assignment_title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this assignment!')
    
    return redirect('course_detail', course_id=course_id)

@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submission = None
    
    if request.user.role == 'student':
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    submissions = None
    if request.user.role in ['teacher', 'admin']:
        submissions = assignment.submissions.all()
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'submissions': submissions,
    }
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if assignment.is_deadline_passed():
        messages.error(request, 'Submission deadline has passed!')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    if Submission.objects.filter(assignment=assignment, student=request.user).exists():
        messages.error(request, 'You have already submitted this assignment!')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        answer_file = request.FILES.get('answer_file')
        
        if not answer_text and not answer_file:
            messages.error(request, 'Please provide either text answer or upload a file!')
            return redirect('submit_assignment', assignment_id=assignment.id)
        
        Submission.objects.create(
            assignment=assignment,
            student=request.user,
            answer_text=answer_text,
            answer_file=answer_file
        )
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('assignment_detail', assignment_id=assignment.id)
    
    return render(request, 'assignments/submit_assignment.html', {'assignment': assignment})

@user_passes_test(is_teacher)
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        marks = request.POST.get('marks')
        feedback = request.POST.get('feedback')
        
        submission.marks = marks
        submission.feedback = feedback
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, 'Grade saved successfully!')
        return redirect('assignment_detail', assignment_id=submission.assignment.id)
    
    return render(request, 'assignments/grade_submission.html', {'submission': submission})
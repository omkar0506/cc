import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user, logout_user
from app.extensions import db
from app.auth.decorators import candidate_required
from app.models.user import User, CandidateProfile
from app.models.interview import InterviewSession
from app.models.resume import Resume
from app.models.evaluation import SkillEvidence
from app.models.learning import LearningItem
from app.models.admin import AuditLog
from app.candidate.forms import ProfileForm, ChangePasswordForm, DeleteAccountForm

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidate')


@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    """Candidate overview dashboard with real DB-backed metrics."""
    sessions = InterviewSession.query.filter_by(
        candidate_id=current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()

    completed_sessions = [s for s in sessions if s.status == 'completed']
    scores = [s.overall_score for s in completed_sessions if s.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    best_score = round(max(scores), 2) if scores else 0.0

    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    evidence_items = SkillEvidence.query.filter_by(candidate_id=current_user.id).all()
    learning_items = LearningItem.query.filter_by(candidate_id=current_user.id).order_by(LearningItem.priority_score.desc()).all()

    return render_template(
        'candidate/dashboard.html',
        sessions=sessions,
        completed_sessions=completed_sessions,
        avg_score=avg_score,
        best_score=best_score,
        resumes=resumes,
        evidence_items=evidence_items,
        learning_items=learning_items
    )


@candidate_bp.route('/profile', methods=['GET', 'POST'])
@candidate_required
def profile():
    """Candidate profile editing and password updates."""
    profile_record = current_user.profile
    if not profile_record:
        profile_record = CandidateProfile(user_id=current_user.id, full_name=current_user.email.split('@')[0])
        db.session.add(profile_record)
        db.session.commit()

    profile_form = ProfileForm(obj=profile_record)
    password_form = ChangePasswordForm()
    delete_form = DeleteAccountForm()

    if 'profile_submit' in request.form and profile_form.validate_on_submit():
        profile_record.full_name = profile_form.full_name.data.strip()
        profile_record.phone = profile_form.phone.data.strip() if profile_form.phone.data else None
        profile_record.headline = profile_form.headline.data.strip() if profile_form.headline.data else None
        profile_record.education_level = profile_form.education_level.data.strip() if profile_form.education_level.data else None
        profile_record.institution = profile_form.institution.data.strip() if profile_form.institution.data else None
        profile_record.graduation_year = profile_form.graduation_year.data
        profile_record.bio = profile_form.bio.data.strip() if profile_form.bio.data else None

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('candidate.profile'))

    if 'password_submit' in request.form and password_form.validate_on_submit():
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('candidate.profile'))
        else:
            flash('Current password was incorrect.', 'danger')

    return render_template(
        'candidate/profile.html',
        profile_form=profile_form,
        password_form=password_form,
        delete_form=delete_form,
        profile=profile_record
    )


@candidate_bp.route('/export-data')
@candidate_required
def export_data():
    """Export all personal candidate data in compliant JSON format."""
    user = current_user
    profile_data = {
        'full_name': user.profile.full_name if user.profile else None,
        'email': user.email,
        'phone': user.profile.phone if user.profile else None,
        'headline': user.profile.headline if user.profile else None,
        'education_level': user.profile.education_level if user.profile else None,
        'institution': user.profile.institution if user.profile else None,
        'graduation_year': user.profile.graduation_year if user.profile else None,
        'bio': user.profile.bio if user.profile else None,
        'registered_at': user.created_at.isoformat()
    }

    sessions_data = []
    for s in user.interview_sessions:
        sessions_data.append({
            'session_uuid': s.session_uuid,
            'role': s.job_role.title if s.job_role else None,
            'category': s.category,
            'status': s.status,
            'overall_score': s.overall_score,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'completed_at': s.completed_at.isoformat() if s.completed_at else None,
        })

    resumes_data = []
    for r in user.resumes:
        resumes_data.append({
            'original_filename': r.original_filename,
            'file_size_bytes': r.file_size_bytes,
            'status': r.status,
            'uploaded_at': r.created_at.isoformat()
        })

    evidence_data = []
    for ev in user.skill_evidence:
        evidence_data.append({
            'skill': ev.skill.name if ev.skill else None,
            'status': ev.status,
            'resume_claim': ev.resume_claim,
            'self_rating': ev.self_rating,
            'average_score_ratio': ev.average_score_ratio,
            'sufficiency_note': ev.sufficiency_note
        })

    export_payload = {
        'candidate_profile': profile_data,
        'interview_sessions': sessions_data,
        'resumes': resumes_data,
        'skill_evidence': evidence_data
    }

    # Audit export
    audit = AuditLog(
        user_id=user.id,
        action='DATA_EXPORT',
        target_type='users',
        target_id=str(user.id),
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    response = jsonify(export_payload)
    response.headers['Content-Disposition'] = f'attachment; filename=candidate_data_{user.id}.json'
    return response


@candidate_bp.route('/delete-account', methods=['POST'])
@candidate_required
def delete_account():
    """Permanently delete candidate account, private files, and associated records."""
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm_phrase.data != 'DELETE':
            flash('Please type "DELETE" exactly to confirm account deletion.', 'danger')
            return redirect(url_for('candidate.profile'))

        if not current_user.check_password(form.password.data):
            flash('Incorrect password. Account was not deleted.', 'danger')
            return redirect(url_for('candidate.profile'))

        user_id = current_user.id
        # Remove stored resume files from filesystem
        for resume in current_user.resumes:
            if resume.file_path and os.path.exists(resume.file_path):
                try:
                    os.remove(resume.file_path)
                except OSError:
                    pass

        # Record audit log before deleting user (set user_id=None so log persists)
        audit = AuditLog(
            user_id=None,
            action='ACCOUNT_DELETED',
            target_type='users',
            target_id=str(user_id),
            details={'email': current_user.email},
            ip_address=request.remote_addr
        )
        db.session.add(audit)

        # Delete user (cascades to profile, sessions, answers, evaluations, skill_evidence)
        db.session.delete(current_user)
        db.session.commit()

        logout_user()
        flash('Your account and all associated data have been permanently deleted.', 'info')
        return redirect(url_for('main.index'))

    flash('Could not validate deletion request.', 'danger')
    return redirect(url_for('candidate.profile'))

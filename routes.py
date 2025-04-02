from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Quiz, Question, QuizAttempt, Analytics
from app import db
from utils.analytics import get_user_stats, get_quiz_stats, get_global_analytics
from utils.report_generator import generate_quiz_report, generate_user_report, export_quiz_results

def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        """Homepage route"""
        total_quizzes = Quiz.query.filter_by(is_public=True).count()
        total_users = User.query.count()
        recent_quizzes = Quiz.query.filter_by(is_public=True).order_by(Quiz.created_at.desc()).limit(5).all()
        
        return render_template('index.html', 
                            total_quizzes=total_quizzes,
                            total_users=total_users,
                            recent_quizzes=recent_quizzes)
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard route for logged-in users"""
        user_stats = get_user_stats(current_user.id)
        created_quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
        recent_attempts = QuizAttempt.query.filter_by(
            user_id=current_user.id,
            is_completed=True
        ).order_by(QuizAttempt.end_time.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                            user=current_user,
                            stats=user_stats,
                            created_quizzes=created_quizzes,
                            recent_attempts=recent_attempts)
    
    @app.route('/quizzes')
    def quizzes():
        """List all public quizzes"""
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        quizzes = Quiz.query.filter_by(is_public=True).order_by(
            Quiz.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return render_template('quizzes.html', quizzes=quizzes)
    
    @app.route('/quiz/<int:quiz_id>')
    def quiz_details(quiz_id):
        """Show details for a specific quiz"""
        quiz = Quiz.query.get_or_404(quiz_id)
        creator = User.query.get(quiz.creator_id)
        
        total_attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id, is_completed=True).count()
        avg_score = quiz.get_average_score()
        
        return render_template('quiz_details.html',
                            quiz=quiz,
                            creator=creator,
                            total_attempts=total_attempts,
                            avg_score=avg_score)
    
    @app.route('/reports')
    @login_required
    def reports():
        """Show available reports"""
        user_quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
        attempted_quizzes = QuizAttempt.query.filter_by(
            user_id=current_user.id,
            is_completed=True
        ).all()
        
        return render_template('reports.html',
                            user_quizzes=user_quizzes,
                            attempted_quizzes=attempted_quizzes)
    
    @app.route('/reports/quiz/<int:quiz_id>')
    @login_required
    def quiz_report(quiz_id):
        """Generate and display a quiz report"""
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Check if user is the creator or an admin
        if quiz.creator_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to view this report.')
            return redirect(url_for('quizzes'))
        
        report_data = generate_quiz_report(quiz_id)
        
        return render_template('report_template.html',
                            quiz=quiz,
                            report=report_data,
                            report_type='quiz')
    
    @app.route('/reports/user/<int:user_id>')
    @login_required
    def user_report(user_id):
        """Generate and display a user report"""
        user = User.query.get_or_404(user_id)
        
        # Check if requesting own report or is admin
        if user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to view this report.')
            return redirect(url_for('dashboard'))
        
        report_data = generate_user_report(user_id)
        
        return render_template('report_template.html',
                            user=user,
                            report=report_data,
                            report_type='user')
    
    # API Endpoints
    @app.route('/api/quiz/<int:quiz_id>/stats')
    def api_quiz_stats(quiz_id):
        """API endpoint to get quiz statistics"""
        stats = get_quiz_stats(quiz_id)
        return jsonify(stats)
    
    @app.route('/api/user/<int:user_id>/stats')
    def api_user_stats(user_id):
        """API endpoint to get user statistics"""
        stats = get_user_stats(user_id)
        return jsonify(stats)
    
    @app.route('/api/analytics')
    def api_analytics():
        """API endpoint to get global analytics"""
        days = request.args.get('days', 30, type=int)
        analytics = get_global_analytics(days)
        return jsonify(analytics)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        return render_template('error.html', error_code=404, message="Page not found"), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 errors"""
        return render_template('error.html', error_code=403, message="Access forbidden"), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 errors"""
        return render_template('error.html', error_code=500, message="Internal server error"), 500

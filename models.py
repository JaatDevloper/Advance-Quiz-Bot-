from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """User model representing Telegram users of the bot"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    created_quizzes = relationship('Quiz', back_populates='creator')
    quiz_attempts = relationship('QuizAttempt', back_populates='user')
    
    def __repr__(self):
        return f"<User id={self.id} telegram_id={self.telegram_id} username={self.username}>"

class Quiz(db.Model):
    """Quiz model containing quiz metadata and settings"""
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_public = Column(Boolean, default=True)
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    time_limit = Column(Integer, default=30)  # Seconds per question
    allow_negative_marking = Column(Boolean, default=False)
    negative_marking_factor = Column(Float, default=0.25)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(String(256), nullable=True)
    sections = Column(JSON, default={})  # For organizing questions into sections
    
    creator = relationship('User', back_populates='created_quizzes')
    questions = relationship('Question', back_populates='quiz', cascade="all, delete-orphan")
    attempts = relationship('QuizAttempt', back_populates='quiz', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quiz id={self.id} title={self.title} questions={len(self.questions)}>"
    
    def get_total_questions(self):
        return len(self.questions)
    
    def get_average_score(self):
        if not self.attempts:
            return 0
        
        completed_attempts = [a for a in self.attempts if a.is_completed]
        if not completed_attempts:
            return 0
        
        total_percentage = 0
        for attempt in completed_attempts:
            if attempt.max_score > 0:
                total_percentage += (attempt.score / attempt.max_score) * 100
        
        return total_percentage / len(completed_attempts)

class Question(db.Model):
    """Question model representing individual quiz questions"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List of options
    correct_option = Column(Integer, nullable=False)  # Index of correct option
    explanation = Column(Text, nullable=True)  # Explanation for the correct answer
    points = Column(Integer, default=1)
    section = Column(String(64), nullable=True)  # Section name if quiz is organized in sections
    order = Column(Integer, default=0)  # Order in the quiz
    
    quiz = relationship('Quiz', back_populates='questions')
    answers = relationship('Answer', back_populates='question', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question id={self.id} quiz_id={self.quiz_id}>"

class QuizAttempt(db.Model):
    """Model for tracking user's quiz attempts"""
    __tablename__ = 'quiz_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    section_scores = Column(JSON, default={})  # Scores by section
    
    user = relationship('User', back_populates='quiz_attempts')
    quiz = relationship('Quiz', back_populates='attempts')
    answers = relationship('Answer', back_populates='attempt', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuizAttempt id={self.id} user_id={self.user_id} quiz_id={self.quiz_id} score={self.score}/{self.max_score}>"
    
    def calculate_score(self):
        """Calculates the score for this attempt"""
        total_score = 0
        max_possible = 0
        
        for answer in self.answers:
            question = answer.question
            max_possible += question.points
            
            if answer.is_correct:
                total_score += question.points
            elif self.quiz.allow_negative_marking:
                # Apply negative marking if enabled
                penalty = question.points * self.quiz.negative_marking_factor
                total_score -= penalty
        
        self.score = total_score
        self.max_score = max_possible
        return total_score

class Answer(db.Model):
    """Model to store user's answers to questions"""
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    selected_option = Column(Integer, nullable=True)  # Index of selected option
    is_correct = Column(Boolean, default=False)
    answer_time = Column(DateTime, default=datetime.utcnow)
    time_taken = Column(Integer, nullable=True)  # Time taken in seconds
    
    attempt = relationship('QuizAttempt', back_populates='answers')
    question = relationship('Question', back_populates='answers')
    
    def __repr__(self):
        return f"<Answer id={self.id} attempt_id={self.attempt_id} question_id={self.question_id} is_correct={self.is_correct}>"

class ChatGroup(db.Model):
    """Model for tracking Telegram groups where the bot is active"""
    __tablename__ = 'chat_groups'
    
    id = Column(Integer, primary_key=True)
    telegram_chat_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatGroup id={self.id} telegram_chat_id={self.telegram_chat_id} title={self.title}>"

class QuizSession(db.Model):
    """Model for tracking active quiz sessions in progress"""
    __tablename__ = 'quiz_sessions'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    chat_id = Column(Integer, nullable=False)  # Telegram chat ID
    current_question_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    marathon_mode = Column(Boolean, default=False)
    
    quiz = relationship('Quiz')
    
    def __repr__(self):
        return f"<QuizSession id={self.id} quiz_id={self.quiz_id} chat_id={self.chat_id} is_active={self.is_active}>"

class Analytics(db.Model):
    """Model for storing analytics data"""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    chat_id = Column(Integer, nullable=True)
    event_type = Column(String(64), nullable=False)  # e.g., "quiz_start", "question_answer", "quiz_complete"
    event_data = Column(JSON, default={})
    
    quiz = relationship('Quiz')
    user = relationship('User')
    
    def __repr__(self):
        return f"<Analytics id={self.id} event_type={self.event_type} date={self.date}>"

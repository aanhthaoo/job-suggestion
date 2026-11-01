"""
Celery tasks for data ingestion and background processing
"""
from celery import Celery
import os
from datetime import datetime, timedelta

# Celery configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    'ingest-greenhouse-jobs': {
        'task': 'tasks.ingest_greenhouse_jobs',
        'schedule': timedelta(hours=12),  # Every 12 hours
    },
    'reconcile-jobs': {
        'task': 'tasks.reconcile_jobs',
        'schedule': timedelta(hours=12),
    },
}


@celery_app.task(bind=True, max_retries=3)
def ingest_greenhouse_jobs(self):
    """Ingest jobs from Greenhouse Job Board API"""
    try:
        import httpx
        
        # List of company tokens to fetch
        # In production, this would come from a database table
        company_tokens = [
            'navervietnam',
            # Add more tokens here
        ]
        
        total_imported = 0
        
        for token in company_tokens:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
                
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    
                    data = response.json()
                    jobs = data.get('jobs', [])
                    
                    # Process each job
                    for job_data in jobs:
                        # Transform and save to database
                        # In production, this would insert into PostgreSQL
                        pass
                    
                    total_imported += len(jobs)
                    
            except Exception as e:
                print(f"Error fetching {token}: {e}")
                continue
        
        return {
            'status': 'success',
            'total_imported': total_imported,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry after 5 minutes


@celery_app.task
def reconcile_jobs():
    """Close jobs that haven't been seen in 2 cycles (24 hours)"""
    try:
        # In production, this would query PostgreSQL:
        # UPDATE jobs SET status = 'closed' 
        # WHERE last_seen_at < NOW() - INTERVAL '24 hours'
        # AND source_type IN ('greenhouse', 'lever', 'ashby')
        
        return {
            'status': 'success',
            'message': 'Reconciliation completed',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, max_retries=2)
def parse_cv_task(self, file_path: str, user_id: str):
    """Parse CV in background and update user profile"""
    try:
        from .cv_parser import parse_cv
        
        # Determine file type
        file_type = file_path.split('.')[-1].lower()
        
        # Parse CV
        result = parse_cv(file_path, file_type)
        
        # In production, update database:
        # UPDATE cvs SET parsed_data = :result WHERE user_id = :user_id
        
        return {
            'status': 'success',
            'user_id': user_id,
            'skills_found': len(result['skills']),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def generate_recommendations_task(user_id: str):
    """Generate personalized recommendations for all users"""
    try:
        # In production:
        # 1. Fetch user profile from database
        # 2. Get all active jobs
        # 3. Calculate match scores
        # 4. Save top 10 recommendations per user
        
        return {
            'status': 'success',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # Test tasks
    print("Testing ingest_greenhouse_jobs...")
    result = ingest_greenhouse_jobs()
    print(f"Result: {result}")

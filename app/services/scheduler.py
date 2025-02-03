from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.db.session import get_db_context
from app.services.notifications import NotificationService
from app.db.models import User

scheduler = AsyncIOScheduler()

async def check_all_notifications():
    """Verifica todas as notificações para todos os usuários"""
    with get_db_context() as db:
        users = db.query(User).filter(User.is_active == True).all()
        notification_service = NotificationService()
        
        for user in users:
            await notification_service.check_bills(user, db)
            await notification_service.check_balance_alerts(user, db)
            await notification_service.check_goals(user, db)

def setup_scheduler():
    """Configura as tarefas agendadas"""
    # Verifica contas a pagar todos os dias às 9h
    scheduler.add_job(
        check_all_notifications,
        CronTrigger(hour=9, minute=0)
    )
    
    # Envia relatório mensal no primeiro dia do mês
    scheduler.add_job(
        send_monthly_reports,
        CronTrigger(day=1, hour=8, minute=0)
    )
    
    scheduler.start() 
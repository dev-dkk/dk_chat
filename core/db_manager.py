from sqlalchemy.orm import Session
from .models import ChatMessage, ChatSession, SessionLocal, create_db_and_tables
from datetime import datetime
from contextlib import contextmanager # ADICIONADO

# Garante que as tabelas sejam criadas quando este módulo for importado pela primeira vez
create_db_and_tables()

@contextmanager # ADICIONADO
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_chat_session(db: Session) -> ChatSession:
    db_session = ChatSession(start_time=datetime.utcnow())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def save_message(db: Session, session_id: int, sender: str, text: str):
    db_message = ChatMessage(session_id=session_id, sender=sender, text=text)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_for_session(db: Session, session_id: int):
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()

def get_last_session(db: Session) -> ChatSession | None:
    return db.query(ChatSession).order_by(ChatSession.start_time.desc()).first()

def clear_chat_history_for_session(db: Session, session_id: int):
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()

def delete_session_and_messages(db: Session, session_id: int):
    # Primeiro, exclui as mensagens associadas
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(synchronize_session=False)
    # Depois, exclui a sessão
    db.query(ChatSession).filter(ChatSession.id == session_id).delete(synchronize_session=False)
    db.commit()
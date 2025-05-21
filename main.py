import flet as ft
import os
from ui.splash_screen import SplashScreen
from ui.chat_screen import ChatScreen
from core.db_manager import get_db, create_chat_session, get_last_session

# Definir o diretório de assets
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets'))

def main(page: ft.Page):
    page.title = "DK Chat"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_resizable = True
    
    if os.path.exists(ASSETS_DIR):
        page.assets_dir = ASSETS_DIR
        print(f"DK Chat: Diretório de assets configurado: {ASSETS_DIR}")
    else:
        print(f"AVISO: Diretório de assets não encontrado em {ASSETS_DIR}. Logos e imagens podem não carregar.")

    current_session_id = None

    def get_or_create_current_session():
        nonlocal current_session_id
        with get_db() as db:
            if current_session_id is None:
                session = create_chat_session(db)
                current_session_id = session.id
                print(f"DK Chat: Nova sessão de chat iniciada: ID {current_session_id}")
            else:
                print(f"DK Chat: Usando sessão de chat existente: ID {current_session_id}")
        return current_session_id

    def route_change(route):
        page.views.clear()
        
        page.views.append(
            SplashScreen(page, start_chat_action)
        )

        if page.route == "/chat":
            session_id_for_chat = get_or_create_current_session()
            page.views.append(
                ChatScreen(page, session_id_for_chat)
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def start_chat_action():
        page.go("/chat")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    from core.models import create_db_and_tables
    create_db_and_tables()
    
    # Passe assets_dir para ft.app também, especialmente útil para builds web/desktop
    ft.app(target=main, assets_dir=ASSETS_DIR)
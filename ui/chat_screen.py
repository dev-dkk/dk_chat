import flet as ft
from core.chat_logic import DKChatLogic
from core.db_manager import get_db, save_message, get_messages_for_session, clear_chat_history_for_session
from ui.chat_bubble import ChatBubble
from datetime import datetime

class ChatScreen(ft.View):
    def __init__(self, page: ft.Page, session_id: int):
        super().__init__(route="/chat")
        self.page = page
        self.session_id = session_id
        self.chat_logic = DKChatLogic()

        self.appbar = ft.AppBar(
            title=ft.Text("DK Chat", weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE10),
            actions=[
                ft.IconButton(
                    ft.icons.DELETE_SWEEP_OUTLINED,
                    tooltip="Limpar Chat Atual",
                    on_click=self._confirm_clear_chat,
                    icon_color=ft.colors.RED_ACCENT_200
                ),
                ft.IconButton(
                    ft.icons.HOME_OUTLINED,
                    tooltip="Voltar para Início",
                    on_click=lambda _: self.page.go("/"),
                    icon_color=ft.colors.BLUE_GREY_200
                ),
            ]
        )

        self.chat_list = ft.ListView(
            expand=True,
            spacing=12,
            auto_scroll=True,
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
        )

        self.new_message_field = ft.TextField(
            hint_text="Digite sua mensagem...",
            expand=True,
            filled=True,
            border_radius=25,
            border_color=ft.colors.with_opacity(0.3, ft.colors.BLUE_GREY_300),
            focused_border_color=ft.colors.BLUE_ACCENT_200,
            on_submit=self._send_message_click,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=12),
            text_size=14,
        )

        self.send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            tooltip="Enviar Mensagem",
            on_click=self._send_message_click,
            icon_size=28,
            icon_color=ft.colors.BLUE_ACCENT_200,
        )
        
        self.status_indicator = ft.Container( 
            content=ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2.5, color=ft.colors.BLUE_ACCENT_100), 
                    ft.Text("DK Chat está pensando...", size=12, color=ft.colors.WHITE60)
                ],
                alignment=ft.MainAxisAlignment.CENTER, 
                spacing=10
            ),
            padding=ft.padding.only(top=5), 
            visible=False, 
            alignment=ft.alignment.center 
        )

        self.controls = [
            self.appbar,
            self.chat_list,
            self.status_indicator, 
            ft.Container(
                content=ft.Row(
                    [self.new_message_field, self.send_button],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(left=20, right=10, bottom=15, top=10),
            )
        ]
        self._load_chat_history()

    def _show_status(self, is_thinking: bool):
        self.status_indicator.visible = is_thinking
        self.new_message_field.disabled = is_thinking
        self.send_button.disabled = is_thinking
        self.page.update()

    def _add_message_to_view(self, message_text: str, sender: str, timestamp_dt: datetime = None):
        if timestamp_dt is None:
            timestamp_dt = datetime.now()
        timestamp_str = timestamp_dt.strftime("%d/%m/%Y %H:%M") 
        
        current_page_width = self.page.width if self.page and self.page.width else 700 
        
        calculated_bubble_width = int(current_page_width * 0.70) 

        min_bubble_width = 150  
        max_bubble_width = 550  

        if calculated_bubble_width < min_bubble_width:
            actual_bubble_width = min_bubble_width
        elif calculated_bubble_width > max_bubble_width:
            actual_bubble_width = max_bubble_width
        else:
            actual_bubble_width = calculated_bubble_width
        
        if current_page_width < 400 and actual_bubble_width < current_page_width * 0.85:
            test_width = int(current_page_width * 0.85)
            actual_bubble_width = min(test_width, max_bubble_width)

        bubble = ChatBubble(
            message_text, 
            sender, 
            timestamp_str, 
            bubble_max_width=actual_bubble_width 
        )
        self.chat_list.controls.append(bubble)
        self.page.update() 

    def _send_message_click(self, e):
        user_message = self.new_message_field.value.strip()
        if not user_message:
            return

        self._add_message_to_view(user_message, "user")
        
        with get_db() as db:
            save_message(db, self.session_id, "user", user_message)
        
        self.new_message_field.value = "" 
        self.page.update() 

        self._show_status(True) 

        current_conversation_history = []
        with get_db() as db:
            messages_from_db = get_messages_for_session(db, self.session_id)
            for msg in messages_from_db:
                current_conversation_history.append({"sender": msg.sender, "text": msg.text})
        
        try:
            bot_response = self.chat_logic.get_response(user_message, current_conversation_history)
        except Exception as ex:
            print(f"Erro crítico ao obter resposta do bot: {ex}")
            bot_response = f"Ocorreu um erro crítico ao processar sua solicitação: {ex}"
        finally:
            self._show_status(False) 
            self.new_message_field.focus() 

        self._add_message_to_view(bot_response, "dk_chat")
        with get_db() as db:
            save_message(db, self.session_id, "dk_chat", bot_response)
        
        self.page.update() 

    def _load_chat_history(self):
        self.chat_list.controls.clear() 
        with get_db() as db:
            messages = get_messages_for_session(db, self.session_id)
            for msg in messages:
                # Ao carregar o histórico, também precisamos calcular a largura da bolha
                self._add_message_to_view(msg.text, msg.sender, msg.timestamp)
        self.page.update()

    def _confirm_clear_chat(self, e):
        def close_dialog(e_dialog):
            confirm_dialog.open = False
            self.page.update()

        def handle_confirm_clear(e_dialog):
            with get_db() as db:
                clear_chat_history_for_session(db, self.session_id)
            
            self.chat_list.controls.clear()
            # Adiciona uma mensagem informativa que não será salva no histórico do DB
            # Precisamos calcular a largura da bolha para esta mensagem também
            current_page_width = self.page.width if self.page and self.page.width else 700
            calculated_bubble_width = int(current_page_width * 0.70)
            min_bubble_width = 150
            max_bubble_width = 550
            if calculated_bubble_width < min_bubble_width: actual_bubble_width = min_bubble_width
            elif calculated_bubble_width > max_bubble_width: actual_bubble_width = max_bubble_width
            else: actual_bubble_width = calculated_bubble_width
            if current_page_width < 400 and actual_bubble_width < current_page_width * 0.85:
                test_width = int(current_page_width * 0.85)
                actual_bubble_width = min(test_width, max_bubble_width)

            info_bubble = ChatBubble(
                "Histórico de chat limpo.", 
                "dk_chat", 
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                bubble_max_width=actual_bubble_width
            )
            self.chat_list.controls.append(info_bubble)
            
            close_dialog(e_dialog)
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Limpeza do Chat"),
            content=ft.Text("Você tem certeza que deseja limpar o histórico desta conversa? Esta ação não pode ser desfeita."),
            actions=[
                ft.TextButton("Sim, limpar", on_click=handle_confirm_clear, style=ft.ButtonStyle(color=ft.colors.RED_ACCENT_400)),
                ft.TextButton("Cancelar", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10), 
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()
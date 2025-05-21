import flet as ft

class ChatBubble(ft.Row):
    def __init__(self, message: str, sender: str, timestamp: str, bubble_max_width: int):
        super().__init__(expand=True) 
        
        self.vertical_alignment = ft.CrossAxisAlignment.START
        is_user = sender == "user"

        # Controle para exibir o ícone do usuário ou a logo do bot
        sender_display_control: ft.Control # Type hinting

        if is_user:
            sender_display_control = ft.Icon(
                name=ft.icons.PERSON_OUTLINE,
                color=ft.colors.BLUE_ACCENT_200,
                size=30
            )
        else: # DK Chat (bot)
            sender_display_control = ft.Image(
                src="/logo.png",  # Assume que sua logo se chama 'logo.png' e está na pasta assets.
                                  # A barra '/' no início faz o Flet procurar na raiz do assets_dir.
                width=30,
                height=30,
                fit=ft.ImageFit.CONTAIN, # Garante que a imagem caiba sem distorção.
                                         # Outras opções: COVER, FILL, SCALE_DOWN, NONE
                # border_radius=ft.border_radius.all(15) # Opcional: se sua logo for quadrada e você quiser torná-la circular
                                                          # ou com cantos arredondados.
            )

        message_content = ft.Text(
            message,
            selectable=True,
        )

        bubble_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(sender.capitalize(), weight=ft.FontWeight.BOLD, size=12),
                    message_content,
                    ft.Text(timestamp, size=10, color=ft.colors.WHITE54, italic=True, text_align=ft.TextAlign.RIGHT)
                ],
                spacing=5,
            ),
            bgcolor=ft.colors.with_opacity(0.15, ft.colors.BLUE_GREY_700) if is_user else ft.colors.with_opacity(0.1, ft.colors.GREEN_ACCENT_700),
            padding=10,
            border_radius=ft.border_radius.all(15),
            width=bubble_max_width,
        )

        if is_user:
            self.controls = [ft.Container(expand=True, content=None), bubble_container, sender_display_control]
        else:
            self.controls = [sender_display_control, bubble_container, ft.Container(expand=True, content=None)]
        
        self.spacing = 10
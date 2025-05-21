import flet as ft

class SplashScreen(ft.View):
    def __init__(self, page: ft.Page, start_chat_callback):
        super().__init__(route="/")
        self.page = page
        self.start_chat_callback = start_chat_callback

        # Tenta carregar um logo, senão usa texto
        try:
            # Se você tiver 'assets/logo.png', descomente e ajuste o caminho
            # logo_image = ft.Image(src=f"/assets/logo.png", width=150, height=150)
            # self.page.splash = ft.ProgressBar() # Para carregamento de assets
            # self.page.update()
            # Para usar assets, precisa configurar page.assets_dir no main.py
            logo_element = ft.Text("DK Chat", size=50, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_ACCENT_400)
        except:
            logo_element = ft.Text("DK Chat", size=50, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_ACCENT_400)


        self.controls = [
            ft.Column(
                [
                    ft.Container(height=50), # Espaçador
                    logo_element,
                    ft.Text(
                        "Sua experiência de chat inteligente",
                        size=18,
                        italic=True,
                        color=ft.colors.WHITE70
                    ),
                    ft.Container(height=30), # Espaçador
                    ft.FilledButton(
                        text="Iniciar Chat",
                        icon=ft.icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
                        on_click=lambda _: self.start_chat_callback(), # Chama o callback para mudar de view
                        height=50,
                        width=200,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            bgcolor=ft.colors.BLUE_ACCENT_700,
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True, # Ocupa todo o espaço vertical disponível
                spacing=20
            )
        ]
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai # Adicionado

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Adicionado

NEWS_KEYWORDS = [
    "notícia", "notícias", "hoje", "agora", "recente", "últimas",
    "o que aconteceu", "qual a novidade", "aconteceu com", "previsão do tempo",
    "cotação", "dólar", "bolsa de valores", "resultado de jogo", "quem ganhou"
]

class DKChatLogic:
    def __init__(self):
        self.gemini_model = None
        if not DEEPSEEK_API_KEY:
            print("AVISO: Chave da API DeepSeek não configurada. O modo de busca complementar não funcionará.")
        
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Usaremos o gemini-1.5-flash-latest que é rápido e eficiente para chat.
                # Outras opções: 'gemini-pro', 'gemini-1.5-pro-latest'
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                print("DK Chat: API do Gemini configurada e modelo carregado.")
            except Exception as e:
                print(f"DK Chat: Erro ao configurar API do Gemini: {e}")
                self.gemini_model = None
        else:
            print("AVISO: Chave da API Gemini não configurada. O chat principal usará respostas genéricas.")

    def _should_use_deepseek(self, user_message: str) -> bool:
        if not DEEPSEEK_API_KEY:
            return False
        message_lower = user_message.lower()
        for keyword in NEWS_KEYWORDS:
            if keyword in message_lower:
                return True
        current_year = str(datetime.now().year)
        if "?" in user_message and (current_year in message_lower or "ontem" in message_lower or "esta semana" in message_lower):
            if any(kw in message_lower for kw in ["quando", "quem", "onde", "qual foi"]):
                 return True
        return False

    def _query_deepseek(self, query: str) -> str:
        # (Esta função permanece a mesma de antes)
        if not DEEPSEEK_API_KEY:
            return "Desculpe, não consigo buscar informações online no momento (API DeepSeek não configurada)."
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Você é um assistente prestativo que busca informações atualizadas na web sobre o seguinte tópico."},
                {"role": "user", "content": query}
            ]
        }
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data.get("choices") and len(data["choices"]) > 0 and data["choices"][0].get("message"):
                return data["choices"][0]["message"]["content"].strip()
            return "Não consegui obter uma resposta da DeepSeek."
        except requests.exceptions.RequestException as e:
            print(f"Erro ao chamar a API DeepSeek: {e}")
            return f"Desculpe, tive um problema ao tentar buscar informações online com DeepSeek: {e}"
        except Exception as e:
            print(f"Erro inesperado ao processar resposta da DeepSeek: {e}")
            return "Desculpe, ocorreu um erro inesperado ao processar a busca online com DeepSeek."

    def _query_gemini(self, user_message: str, conversation_history: list[dict]) -> str:
        if not self.gemini_model:
            return "API do Gemini não está configurada ou falhou ao carregar. Usando resposta padrão."

        # Formatar histórico para a API do Gemini
        # A API espera uma lista de dicts: {'role': 'user'/'model', 'parts': [{'text': '...'}]}
        # O histórico deve alternar entre 'user' e 'model'.
        gemini_history = []
        for msg in conversation_history:
            role = "user" if msg["sender"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [{"text": msg["text"]}]})
        
        # Adiciona a mensagem atual do usuário ao final do histórico para o Gemini
        # gemini_history.append({"role": "user", "parts": [{"text": user_message}]}) 
        # A mensagem atual já estará no final de `gemini_history` se `conversation_history` incluir ela.
        # Se `conversation_history` for o histórico *antes* da mensagem atual, então adicione-a.
        # No nosso caso, ChatScreen já está salvando a mensagem do usuário e depois pegando o histórico todo.

        # Opcional: Adicionar uma mensagem de sistema (prompt)
        # system_instruction = "Você é o DK Chat, um assistente prestativo e amigável."
        # Ou, para um chat contínuo, o histórico já serve como contexto.

        try:
            # Para conversas, é melhor iniciar uma sessão de chat
            chat_session = self.gemini_model.start_chat(history=gemini_history)
            response = chat_session.send_message(
                user_message, # Envia apenas a nova mensagem, o histórico já está na sessão
                # safety_settings={ # Opcional: Ajustar configurações de segurança
                #    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                #    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                #    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                #    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                # }
            )

            if not response.candidates: # Resposta pode ter sido bloqueada
                block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Não especificado"
                block_reason_message = response.prompt_feedback.block_reason_message if response.prompt_feedback else ""
                print(f"Resposta do Gemini bloqueada. Razão: {block_reason} - {block_reason_message}")
                for candidate in response.candidates: # Para debug, se houver candidatos mesmo com bloqueio
                    print(f"  Candidato finish_reason: {candidate.finish_reason}, safety_ratings: {candidate.safety_ratings}")

                return f"Minha resposta foi bloqueada pelas políticas de segurança (Razão: {block_reason}). Por favor, reformule sua pergunta ou tente um tópico diferente."
            
            # Para respostas de texto simples
            if response.text:
                return response.text
            else: # Caso inesperado
                return "Recebi uma resposta vazia do Gemini."

        except Exception as e:
            print(f"Erro ao chamar a API Gemini: {e}")
            # Adicionar tratamento para erros específicos de API Key se necessário
            if "API_KEY" in str(e).upper():
                 return "A chave da API do Gemini parece ser inválida ou está com problemas. Verifique suas configurações."
            return f"Desculpe, tive um problema ao tentar me comunicar com o Gemini: {e}"

    def get_response(self, user_message: str, conversation_history: list[dict] = None) -> str:
        """
        Obtém uma resposta para a mensagem do usuário.
        `conversation_history` é uma lista de dicts: [{"sender": "user/dk_chat", "text": "..."}]
        A última mensagem em `conversation_history` é a mensagem atual do usuário.
        """
        if conversation_history is None:
            conversation_history = []

        if self._should_use_deepseek(user_message):
            print("DK Chat: Usando DeepSeek para buscar informação complementar.")
            deepseek_info = self._query_deepseek(user_message)
            
            # Agora, podemos passar essa informação para o Gemini contextualizar
            if self.gemini_model:
                print("DK Chat: Contextualizando informação do DeepSeek com Gemini.")
                # Criar um prompt para o Gemini usar a informação do DeepSeek
                prompt_with_context = (
                    f"Com base na seguinte informação de busca: '{deepseek_info}'.\n\n"
                    f"Responda à pergunta do usuário: '{user_message}'"
                )
                # Para esta chamada específica, não usamos o histórico de chat, apenas a info da busca.
                # Ou, poderíamos adicionar a info da busca ao histórico antes de chamar Gemini.
                # Vamos tentar uma chamada direta ao Gemini com o contexto da busca:
                
                # Formatando para Gemini: o histórico aqui será a informação de busca como contexto do modelo
                # e a pergunta original do usuário.
                contextual_history_for_gemini = [
                    {"role": "user", "parts": [{"text": f"Contexto de busca: {deepseek_info}\n\nPergunta original: {user_message}"}]}
                ]
                # Ou uma forma mais "conversacional" para o Gemini:
                # contextual_history_for_gemini = [
                #    {"role": "model", "parts": [{"text": f"Ok, encontrei esta informação: {deepseek_info}"}]},
                #    {"role": "user", "parts": [{"text": f"Baseado nisso, {user_message}"}]} # Requer que user_message seja uma pergunta sobre o contexto
                # ]
                # Simplesmente passar a info para o Gemini responder é mais direto:

                try:
                    chat_session = self.gemini_model.start_chat(history=[]) # Sem histórico de chat para esta chamada específica
                    response = chat_session.send_message(prompt_with_context)
                    if response.text:
                        return response.text
                    else:
                        return f"(Informação da busca: {deepseek_info})\n\nNão consegui contextualizar com Gemini. Tente perguntar diretamente."
                except Exception as e:
                    print(f"Erro ao contextualizar com Gemini: {e}")
                    return f"(Informação da busca: {deepseek_info})\n\nOcorreu um erro ao tentar usar Gemini para contextualizar."
            else: # Se Gemini não estiver configurado, retorna apenas a info do DeepSeek
                return deepseek_info
        
        # Se não for usar DeepSeek, ou se Gemini for usado para contextualizar
        elif self.gemini_model:
            print("DK Chat: Usando Gemini para resposta geral.")
            # O histórico completo (incluindo a última mensagem do usuário) é passado.
            # Gemini _query_gemini espera o histórico completo e a última mensagem separada.
            # Ajuste: passar o histórico *sem* a última mensagem, e a última mensagem separada.
            
            history_up_to_last_user_msg = []
            if conversation_history and len(conversation_history) > 1: # Se houver mais que a msg atual do usuário
                history_up_to_last_user_msg = conversation_history[:-1]

            return self._query_gemini(user_message, history_up_to_last_user_msg)
        
        else:
            # Fallback se nenhuma API estiver configurada
            print("DK Chat: Nenhuma API de IA configurada. Usando respostas de fallback simples.")
            if "olá" in user_message.lower() or "oi" in user_message.lower():
                return "Olá! Como posso ajudar você hoje? (APIs não configuradas)"
            return "Desculpe, minhas capacidades de IA não estão configuradas no momento."
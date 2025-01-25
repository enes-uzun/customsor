import openai
import streamlit as st
import json
import config
import base64
import logging
import os
from itertools import cycle

# API anahtarları döngüsü
api_keys_cycle = cycle(config.openai_api_keys)

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# windows_user = os.getlogin()  # Bu satırı kaldırın veya aşağıdaki gibi değiştirin
windows_user = "user"  # Sabit bir değer kullanın
logger.info(f"Chat initiated by Windows user: {windows_user}")

# JSON dosyalarını yükleme fonksiyonu
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Base64 formatında resim verisini almak için fonksiyon
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# JSON dosyalarını yükleyin
veri = load_json('knowledges/tum_veriler.json')

# Base64 formatında logo resmini alın
image_base64 = get_base64_image("logoYF.png")

st.set_page_config(
    page_title="Customsor Test HS Code Finder Chatbot",  # Sekme başlığı
    page_icon="🏢"  # Sekme simgesi
)

# Başlık ve logo için HTML ve CSS
st.markdown(f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{image_base64}" alt="Logo" style="height: 80px; margin-bottom: 10px;">
        <h1>Customsor Test HS Code Finder Chatbot</h1>
    </div>
    """, unsafe_allow_html=True)

# Sohbet geçmişi için bir liste oluşturun
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sohbet geçmişini görüntüle
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan giriş al
if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    # Kullanıcı mesajını sohbet geçmişine ekleyin
    st.session_state.messages.append({"role": "user", "content": prompt})
    logger.info(f"User input by {windows_user}: {prompt}")  # Kullanıcı girdisini logla

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Döngüsel olarak API anahtarını al
        api_key = next(api_keys_cycle)
        openai.api_key = api_key

        try:
            # OpenAI API'ye istek gönder
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sen Yatırım Finansman için çalışan bir chatbotsun."},
                    {"role": "system", "content": json.dumps(veri)},
                    *st.session_state.messages,
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            # Yanıtı al ve sohbet geçmişine ekleyin
            for event in response:
                event_text = event['choices'][0].get('delta', {}).get('content', '')
                full_response += event_text
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            logger.info(f"Assistant response to {windows_user}: {full_response}")  # Asistan yanıtını logla

        except Exception as e:
            logger.error(f"Error occurred for user {windows_user}: {str(e)}")  # Hataları logla
            st.session_state.messages.append({"role": "assistant", "content": "Bir hata oluştu, lütfen tekrar deneyin."})
            message_placeholder.markdown("Bir hata oluştu, lütfen tekrar deneyin.")

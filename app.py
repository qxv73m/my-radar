import streamlit as st
import requests
import json
import re
import os

# --- НАСТРОЙКИ ---
WEBHOOK_URL = "https://webhook.nodul.ru/28657/dev/6149ffae-eaf6-4f5f-8c50-a383a833bbce"

st.set_page_config(page_title="Upsell & Risk Radar", page_icon="📊")

# --- БЛОК С ЛОГОТИПОМ ---
# Ищем файл logo.png в папке с проектом
if os.path.exists("logo.png"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Если хочешь сделать логотип меньше, замени use_container_width=True на width=300
        st.image("logo.png", use_container_width=True)
else:
    st.warning("⚠️ Файл logo.png не найден в папке с проектом. Положите картинку рядом с этим скриптом.")

# --- ЗАГОЛОВКИ ---
st.title("📊 Upsell & Risk Radar")
st.markdown("Вставьте текст переписки с клиентом, чтобы узнать уровень риска оттока и получить рекомендацию.")

# --- ПОЛЕ ВВОДА ---
user_input = st.text_area(
    "Текст переписки:", 
    height=200, 
    placeholder="Например: Здравствуйте, мы решили не продлевать подписку..."
)

# --- ЛОГИКА АНАЛИЗА ---
if st.button("Анализировать", type="primary"):
    if not user_input.strip():
        st.warning("Пожалуйста, введите текст для анализа.")
    else:
        with st.spinner("Агент анализирует переписку..."):
            try:
                # Отправляем запрос
                response = requests.post(WEBHOOK_URL, json={"text": user_input}, timeout=60)
                response.raise_for_status()
                
                # Получаем сырой ответ
                raw_result = response.json()
                result = None
                
                # Функция для очистки и парсинга JSON
                def extract_json(data):
                    if isinstance(data, dict):
                        if "risk_score" in data:
                            return data
                        for key, value in data.items():
                            found = extract_json(value)
                            if found: return found
                    elif isinstance(data, str):
                        # Очищаем от markdown-тегов
                        clean_str = data.replace('```json', '').replace('```', '').strip()
                        # Ищем JSON-объект
                        match = re.search(r'\{.*\}', clean_str, re.DOTALL)
                        if match:
                            try:
                                parsed = json.loads(match.group())
                                return extract_json(parsed)
                            except:
                                pass
                    return None

                # Извлекаем данные
                result = extract_json(raw_result)

                # Если данные найдены - показываем красиво
                if result and "risk_score" in result:
                    st.success("Анализ завершен!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    risk = result.get("risk_score", 0)
                    with col1:
                        st.metric(label="Уровень риска (1-10)", value=risk)
                    with col2:
                        st.metric(label="Тональность", value=result.get("sentiment", "N/A"))
                    with col3:
                        st.metric(label="Скрытое раздражение", value="Да" if result.get("hidden_irritation") else "Нет")

                    st.divider()

                    st.subheader("💡 Рекомендация по следующему шагу")
                    st.info(result.get("next_step_recommendation", "Рекомендация отсутствует"))

                    st.subheader("🔍 Детали анализа")
                    col_m1, col_m2 = st.columns(2)
                    
                    with col_m1:
                        st.write("**Найденные риски:**")
                        for r in result.get("found_risk_markers", []):
                            st.write(f"- {r}")
                        if not result.get("found_risk_markers"): st.write("Не найдены.")

                    with col_m2:
                        st.write("**Upsell-сигналы:**")
                        for u in result.get("found_upsell_signals", []):
                            st.write(f"- {u}")
                        if not result.get("found_upsell_signals"): st.write("Не найдены.")
                        
                    with st.expander("Посмотреть сырой ответ (для отладки)"):
                        st.json(raw_result)
                else:
                    st.warning("Агент вернул ответ, но в нем нет данных анализа.")
                    st.json(raw_result)

            except Exception as e:
                st.error(f"Ошибка при запросе: {e}")
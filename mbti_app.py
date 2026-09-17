import json
import os
from datetime import date

import streamlit as st

from ai_helper import ask_ai

DATA_FILE = "mbti.json"
APP_TITLE = "우리 반 MBTI 수집소"

# 질문과 라디오 선택지 (질문 4개)
QUESTIONS = [
    {
        "text": "1. 주말에 에너지를 채우는 방법은?",
        "options": ["친구들과 왁자지껄 놀기", "집에서 혼자 조용히 쉬기"],
    },
    {
        "text": "2. 새로운 정보를 받아들일 때 나는?",
        "options": ["구체적인 사실과 경험을 믿는다", "숨은 의미와 가능성을 상상한다"],
    },
    {
        "text": "3. 중요한 결정을 내릴 때 기준은?",
        "options": ["논리와 원칙", "사람의 마음과 관계"],
    },
    {
        "text": "4. 여행을 갈 때 나는?",
        "options": ["계획을 미리 꼼꼼히 세운다", "그때그때 즉흥적으로 움직인다"],
    },
]


def load_data():
    """mbti.json 파일에서 {title, records} 형태의 데이터를 불러온다."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("title", APP_TITLE)
            data.setdefault("records", [])
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"title": APP_TITLE, "records": []}


def save_data(data):
    """데이터를 mbti.json 파일에 저장한다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_result(nick, answers):
    """선택한 답변을 바탕으로 MBTI 유형과 별명, 설명, 해설을 생성한다."""
    qa_text = "\n".join(
        f"- {q['text']} => {ans}" for q, ans in zip(QUESTIONS, answers)
    )
    prompt = f"""너는 재미있는 MBTI 분석가야. 아래는 '{nick}' 학생의 질문별 답변이야.

{qa_text}

이 답변을 바탕으로 이 학생의 MBTI 유형을 추측해서 아래 JSON 형식으로만 답해줘.
다른 말은 절대 붙이지 말고 JSON만 출력해.

{{
  "mbti": "MBTI 4글자 (예: ENFP)",
  "nickname": "이 유형에 어울리는 재미있는 한글 별명",
  "description": "이 학생의 성격을 2~3문장으로 설명",
  "comment": "학생에게 힘이 되는 따뜻한 한 줄 해설"
}}
"""
    raw = ask_ai(prompt)
    return parse_ai_json(raw)


def parse_ai_json(raw):
    """AI 응답에서 JSON 부분을 뽑아 딕셔너리로 변환한다."""
    text = raw.strip()
    # 코드블록(```json ... ```) 안에 들어있는 경우 처리
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    # 중괄호 범위만 추출
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {}
    return {
        "mbti": result.get("mbti", "????"),
        "nickname": result.get("nickname", "알 수 없는 유형"),
        "description": result.get("description", "분석 결과를 불러오지 못했어요."),
        "comment": result.get("comment", ""),
    }


def analyze_class_mood(records):
    """반 친구들의 MBTI 정보를 바탕으로 우리 반 분위기를 분석한다."""
    summary = "\n".join(
        f"- {r['nick']}: {r['mbti']}" for r in records
    )
    prompt = f"""아래는 우리 반 친구들의 MBTI 유형 목록이야.

{summary}

이 정보를 바탕으로 '우리 반 전체의 분위기'를 재미있고 따뜻하게 3~4문장으로 분석해줘.
어떤 성향의 친구들이 많은지, 반 분위기가 어떨지 이야기해줘. JSON 없이 자연스러운 문장으로만 답해줘."""
    return ask_ai(prompt)


# ------------------------- 화면 구성 -------------------------

st.set_page_config(page_title=APP_TITLE, page_icon="🧩")
st.title(f"🧩 {APP_TITLE}")

data = load_data()

# ===== 입력 =====
st.header("📝 나의 MBTI 알아보기")

nick = st.text_input("이름 (또는 별명)")

answers = []
for i, q in enumerate(QUESTIONS):
    choice = st.radio(q["text"], q["options"], key=f"q{i}")
    answers.append(choice)

if st.button("MBTI 분석하기", type="primary"):
    if not nick.strip():
        st.warning("이름을 입력해 주세요!")
    else:
        with st.spinner("AI가 MBTI를 분석하고 있어요..."):
            result = generate_result(nick.strip(), answers)
        record = {
            "nick": nick.strip(),
            "mbti": result["mbti"],
            "answers": answers,
            "day": date.today().isoformat(),
        }
        data["records"].append(record)
        save_data(data)

        st.success(f"{nick.strip()}님의 MBTI는 **{result['mbti']}** ({result['nickname']})!")
        st.write(f"**설명:** {result['description']}")
        if result["comment"]:
            st.info(result["comment"])

st.divider()

# ===== 출력 =====
st.header("👨‍👩‍👧‍👦 우리 반 MBTI 모아보기")

records = data["records"]
st.metric("참여한 친구 수", f"{len(records)}명")

if records:
    table_rows = [
        {
            "이름": r["nick"],
            "MBTI": r["mbti"],
            "답변": " / ".join(r["answers"]),
            "날짜": r["day"],
        }
        for r in records
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.subheader("🔍 우리 반 분위기 분석")
    with st.spinner("우리 반 분위기를 분석하는 중..."):
        mood = analyze_class_mood(records)
    st.write(mood)
else:
    st.info("아직 참여한 친구가 없어요. 첫 번째로 MBTI를 등록해 보세요!")

import streamlit as st
from openai import OpenAI


# =========================
# 1. 기본 페이지 설정
# =========================

st.set_page_config(
    page_title="건강 보조제 정보 챗봇",
    page_icon="💊",
    layout="centered",
)


# =========================
# 2. 건강 보조제 안전 프롬프트
# =========================

SYSTEM_PROMPT = """
너는 한국어로 답변하는 '건강 보조제 및 건강기능식품 정보 챗봇'이다.

너의 역할:
- 건강 보조제, 건강기능식품, 영양 성분에 대한 일반 정보를 제공한다.
- 제품 라벨을 볼 때 확인해야 할 항목을 설명한다.
- 섭취 시 주의해야 할 사람과 상황을 안내한다.
- 사용자가 공식 자료와 전문가 상담을 확인하도록 돕는다.

반드시 지켜야 할 안전 규칙:
1. 질병을 진단하지 않는다.
2. 질병의 치료, 예방, 완치, 개선 효과를 단정하지 않는다.
3. 의약품을 대체하라고 말하지 않는다.
4. 사용자가 복용 중인 약을 중단하거나 변경하라고 말하지 않는다.
5. 특정 보조제를 특정 질병 치료 목적으로 추천하지 않는다.
6. 임신, 수유, 기저질환, 약물 복용, 수술 예정, 알레르기, 어린이·고령자 관련 질문은 반드시 의사 또는 약사 상담을 권한다.
7. 응급 증상으로 보이는 경우에는 보조제 설명보다 즉시 의료기관, 응급실, 119 상담을 우선 안내한다.
8. 복용량은 제품 표시사항, 식약처 인정 내용, 전문가 상담을 기준으로 확인하라고 안내한다.
9. 제품 구매를 과도하게 유도하지 않는다.
10. 모르는 내용은 단정하지 않고 '확인 필요'라고 말한다.
11. 답변은 일반 정보 제공 목적이며 의료 조언이 아님을 필요한 경우 명확히 밝힌다.
12. 한국 사용자를 기준으로 식약처, 식품안전나라, 제품 표시사항 확인을 우선 안내한다.

답변 기본 형식:
- 먼저 질문에 직접 답한다.
- 그다음 아래 구조를 가능한 한 따른다.

[개요]
성분 또는 제품군이 무엇인지 설명한다.

[일반적으로 확인되는 정보]
일반적인 기능성, 영양학적 의미, 소비자가 확인할 부분을 설명한다.
단, 치료 효과처럼 단정하지 않는다.

[주의가 필요한 경우]
약물 복용, 질환, 임신·수유, 수술 예정, 알레르기 등 위험 요소를 설명한다.

[라벨에서 확인할 것]
1일 섭취량, 원료명, 함량, 기능성 내용, 섭취 시 주의사항, 건강기능식품 표시 여부를 안내한다.

[전문가 상담이 필요한 경우]
의사 또는 약사와 상담해야 하는 상황을 구체적으로 안내한다.
"""


# =========================
# 3. 예시용 간단 성분 DB
# 실제 서비스에서는 식약처/식품안전나라/NIH/FDA 등 공식 자료 기반 DB로 교체 권장
# =========================

SUPPLEMENT_KB = {
    "비타민d": {
        "name": "비타민 D",
        "summary": "뼈 건강, 칼슘 흡수와 관련해 자주 언급되는 영양 성분입니다.",
        "caution": "고함량 제품을 장기간 섭취하거나 신장질환, 고칼슘혈증 등이 있는 경우 전문가 상담이 필요합니다.",
        "label": "비타민D 함량, 1일 섭취량, 비타민D 형태, 다른 멀티비타민과의 중복 섭취 여부를 확인하세요.",
    },
    "마그네슘": {
        "name": "마그네슘",
        "summary": "신경과 근육 기능, 에너지 대사와 관련해 자주 언급되는 미네랄입니다.",
        "caution": "신장질환이 있거나 약을 복용 중인 경우, 설사 등 위장 증상이 있는 경우 주의가 필요합니다.",
        "label": "마그네슘 함량, 형태, 1일 섭취량, 다른 미네랄 제품과의 중복 여부를 확인하세요.",
    },
    "오메가3": {
        "name": "오메가3",
        "summary": "EPA, DHA 등 지방산을 포함하는 제품군으로 혈행, 중성지질 등과 관련해 자주 언급됩니다.",
        "caution": "항응고제, 항혈소판제 복용자, 수술 예정자, 출혈 위험이 있는 사람은 전문가 상담이 필요합니다.",
        "label": "EPA/DHA 함량, 1일 섭취량, 원료 어종, 산패 관리, 섭취 시 주의사항을 확인하세요.",
    },
    "프로바이오틱스": {
        "name": "프로바이오틱스",
        "summary": "장 건강과 관련해 자주 사용되는 유산균 제품군입니다.",
        "caution": "면역저하자, 중증질환자, 중심정맥관 보유자 등은 전문가 상담이 필요할 수 있습니다.",
        "label": "균주명, 보장균수, 섭취 기한, 보관 방법, 섭취 시 주의사항을 확인하세요.",
    },
    "루테인": {
        "name": "루테인",
        "summary": "눈 건강 관련 제품에서 자주 사용되는 카로티노이드 성분입니다.",
        "caution": "흡연자, 임신·수유 중인 사람, 다른 눈 건강 제품을 함께 섭취하는 경우 주의가 필요합니다.",
        "label": "루테인 함량, 지아잔틴 포함 여부, 1일 섭취량, 기능성 내용, 주의사항을 확인하세요.",
    },
    "아연": {
        "name": "아연",
        "summary": "정상적인 면역 기능, 세포 분열 등과 관련해 자주 언급되는 미네랄입니다.",
        "caution": "고함량 장기 섭취 시 구리 흡수 저해 등 문제가 생길 수 있어 중복 섭취를 확인해야 합니다.",
        "label": "아연 함량, 1일 섭취량, 멀티비타민과의 중복 여부를 확인하세요.",
    },
    "밀크씨슬": {
        "name": "밀크씨슬",
        "summary": "간 건강 관련 제품에서 자주 보이는 식물성 원료입니다.",
        "caution": "간질환 치료 목적처럼 생각해서는 안 되며, 복용 중인 약이 있거나 간 수치 이상이 있다면 전문가 상담이 필요합니다.",
        "label": "실리마린 함량, 원료명, 1일 섭취량, 섭취 시 주의사항을 확인하세요.",
    },
    "콜라겐": {
        "name": "콜라겐",
        "summary": "피부, 관절, 미용 관련 제품에서 자주 판매되는 단백질 유래 성분입니다.",
        "caution": "알레르기, 원료 출처, 당류나 첨가물 함량을 확인하는 것이 좋습니다.",
        "label": "콜라겐 원료, 분자량 표현, 1일 섭취량, 부원료, 당류 함량을 확인하세요.",
    },
}


# =========================
# 4. 위험 질문 감지용 키워드
# =========================

EMERGENCY_KEYWORDS = [
    "숨이 차", "호흡곤란", "가슴통증", "흉통", "실신", "의식", "기절",
    "심한 두드러기", "얼굴이 부었", "입술이 부었", "목이 부었",
    "아나필락시스", "피를 토", "검은변", "심한 복통", "응급"
]

MEDICATION_KEYWORDS = [
    "혈압약", "당뇨약", "고지혈증약", "항응고제", "와파린", "아스피린",
    "항혈소판제", "항우울제", "수면제", "진통제", "항생제", "스테로이드",
    "약 먹고", "약 복용", "복용 중", "같이 먹어", "함께 먹어", "병용"
]

DISEASE_KEYWORDS = [
    "암", "당뇨", "고혈압", "저혈압", "고지혈증", "신장질환", "콩팥",
    "간질환", "간수치", "갑상선", "우울증", "불안장애", "공황장애",
    "심장병", "부정맥", "위염", "역류성식도염", "과민성대장", "통풍"
]

PREGNANCY_KEYWORDS = [
    "임신", "임산부", "수유", "모유", "출산", "아기", "태아"
]

SURGERY_KEYWORDS = [
    "수술", "시술", "마취", "내시경", "치과수술"
]

CURE_CLAIM_KEYWORDS = [
    "낫", "치료", "완치", "예방", "없애", "고쳐", "약 대신",
    "당뇨에 좋은", "암에 좋은", "고혈압에 좋은"
]


# =========================
# 5. 유틸 함수
# =========================

def normalize_text(text: str) -> str:
    """검색과 위험 감지를 쉽게 하기 위해 소문자/공백 정리"""
    return text.lower().replace(" ", "")


def find_matching_supplements(user_text: str) -> list:
    """질문에 포함된 성분명을 간단히 매칭"""
    normalized = normalize_text(user_text)
    matches = []

    aliases = {
        "비타민d": ["비타민d", "비타민디", "vitamind", "d3", "비타민D"],
        "마그네슘": ["마그네슘", "magnesium"],
        "오메가3": ["오메가3", "오메가-3", "omega3", "epa", "dha"],
        "프로바이오틱스": ["프로바이오틱스", "유산균", "probiotics"],
        "루테인": ["루테인", "lutein"],
        "아연": ["아연", "zinc"],
        "밀크씨슬": ["밀크씨슬", "실리마린", "milkthistle", "silymarin"],
        "콜라겐": ["콜라겐", "collagen"],
    }

    for key, words in aliases.items():
        for word in words:
            if normalize_text(word) in normalized:
                matches.append(key)
                break

    return matches


def keyword_found(user_text: str, keywords: list) -> bool:
    normalized = normalize_text(user_text)
    return any(normalize_text(keyword) in normalized for keyword in keywords)


def classify_risk(user_text: str, profile: dict) -> list:
    """질문 내용과 사용자 상태 체크박스로 위험도를 분류"""
    risks = []

    if keyword_found(user_text, EMERGENCY_KEYWORDS):
        risks.append("응급 가능성")

    if keyword_found(user_text, MEDICATION_KEYWORDS) or profile.get("taking_meds"):
        risks.append("약물 병용 확인 필요")

    if keyword_found(user_text, DISEASE_KEYWORDS) or profile.get("chronic_disease"):
        risks.append("기저질환 관련 확인 필요")

    if keyword_found(user_text, PREGNANCY_KEYWORDS) or profile.get("pregnant_or_lactating"):
        risks.append("임신·수유 관련 확인 필요")

    if keyword_found(user_text, SURGERY_KEYWORDS) or profile.get("surgery_planned"):
        risks.append("수술·시술 전후 섭취 확인 필요")

    if profile.get("allergy"):
        risks.append("알레르기 확인 필요")

    if keyword_found(user_text, CURE_CLAIM_KEYWORDS):
        risks.append("질병 치료·예방 표현 주의")

    return risks


def build_profile_context(profile: dict) -> str:
    """사이드바 체크박스 정보를 모델에게 전달할 텍스트로 변환"""
    selected = []

    if profile.get("taking_meds"):
        selected.append("복용 중인 약 있음")

    if profile.get("pregnant_or_lactating"):
        selected.append("임신 또는 수유 중")

    if profile.get("chronic_disease"):
        selected.append("기저질환 있음")

    if profile.get("surgery_planned"):
        selected.append("수술 또는 시술 예정")

    if profile.get("allergy"):
        selected.append("알레르기 있음")

    if profile.get("child_or_elderly"):
        selected.append("어린이 또는 고령자 관련 질문")

    if not selected:
        return "사용자가 별도의 위험 상태를 선택하지 않았음."

    return "사용자 체크 정보: " + ", ".join(selected)


def build_kb_context(matches: list) -> str:
    """매칭된 성분 정보를 모델에게 참고자료로 전달"""
    if not matches:
        return "질문에서 매칭된 내부 예시 성분 정보 없음."

    blocks = []

    for key in matches:
        item = SUPPLEMENT_KB.get(key)
        if not item:
            continue

        block = f"""
성분명: {item["name"]}
개요: {item["summary"]}
주의사항: {item["caution"]}
라벨 확인사항: {item["label"]}
"""
        blocks.append(block.strip())

    return "\n\n".join(blocks)


def build_risk_context(risks: list) -> str:
    if not risks:
        return "특별한 고위험 신호가 감지되지 않았음. 그래도 일반 정보 제공 원칙을 지킬 것."

    return f"""
감지된 위험 신호:
{", ".join(risks)}

답변 지침:
- 위험 신호를 무시하지 말 것.
- 약물 병용, 질환, 임신·수유, 수술 관련 질문은 안전하게 단정하지 말 것.
- 응급 가능성이 있으면 보조제 설명보다 즉시 의료기관/119/응급실 안내를 우선할 것.
- 치료·예방·완치 효과로 표현하지 말 것.
"""


def make_api_messages(user_prompt: str, profile: dict, max_history: int = 12) -> list:
    """OpenAI API로 보낼 messages 구성"""
    matches = find_matching_supplements(user_prompt)
    risks = classify_risk(user_prompt, profile)

    profile_context = build_profile_context(profile)
    kb_context = build_kb_context(matches)
    risk_context = build_risk_context(risks)

    developer_context = f"""
아래 정보는 현재 사용자 질문에 대한 참고 정보다.

[사용자 상태]
{profile_context}

[내부 예시 성분 정보]
{kb_context}

[위험도 분류]
{risk_context}

중요:
- 내부 예시 성분 정보는 공식 DB가 아니라 MVP용 참고자료다.
- 확실하지 않은 내용은 반드시 확인 필요라고 말한다.
- 기능성, 함량, 섭취량은 제품 표시사항과 공식 자료 확인을 안내한다.
"""

    recent_messages = st.session_state.messages[-max_history:]

    api_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": developer_context},
    ]

    api_messages.extend(
        {"role": m["role"], "content": m["content"]}
        for m in recent_messages
    )

    return api_messages


def stream_openai_response(stream):
    """OpenAI streaming 응답에서 텍스트만 추출"""
    for chunk in stream:
        try:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta and delta.content:
                yield delta.content

        except Exception:
            continue


def get_openai_api_key():
    """Streamlit secrets 또는 사용자 입력에서 API Key 가져오기"""
    secret_key = ""

    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secret_key = ""

    if secret_key:
        return secret_key, "secrets"

    input_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        help="테스트용으로 입력합니다. 실제 배포 시에는 .streamlit/secrets.toml 사용을 권장합니다.",
    )

    return input_key, "input"


# =========================
# 6. 사이드바
# =========================

with st.sidebar:
    st.header("⚙️ 설정")

    api_key, key_source = get_openai_api_key()

    if key_source == "secrets":
        st.success("API Key가 secrets에서 로드되었습니다.")

    model_name = st.text_input(
        "모델명",
        value="gpt-4o-mini",
        help="본인 OpenAI 계정에서 사용 가능한 모델명으로 변경할 수 있습니다.",
    )

    st.divider()

    st.header("🧾 사용자 상태 체크")

    taking_meds = st.checkbox("복용 중인 약이 있음")
    pregnant_or_lactating = st.checkbox("임신 또는 수유 중")
    chronic_disease = st.checkbox("기저질환이 있음")
    surgery_planned = st.checkbox("수술/시술 예정")
    allergy = st.checkbox("알레르기가 있음")
    child_or_elderly = st.checkbox("어린이 또는 고령자 관련 질문")

    user_profile = {
        "taking_meds": taking_meds,
        "pregnant_or_lactating": pregnant_or_lactating,
        "chronic_disease": chronic_disease,
        "surgery_planned": surgery_planned,
        "allergy": allergy,
        "child_or_elderly": child_or_elderly,
    }

    st.divider()

    if st.button("🧹 대화 초기화"):
        st.session_state.messages = []
        st.rerun()

    st.caption(
        "이 앱은 건강 보조제 정보 제공용 MVP입니다. "
        "실제 서비스에서는 공식 데이터베이스, 전문가 검수, 법적 광고 검토가 필요합니다."
    )


# =========================
# 7. 메인 화면
# =========================

st.title("💊 건강 보조제 정보 챗봇")

st.write(
    """
건강 보조제, 건강기능식품, 영양 성분에 대해 질문해보세요.

예시:
- 오메가3는 어떤 사람이 조심해야 하나요?
- 마그네슘은 언제 먹는 게 좋은가요?
- 비타민D를 먹을 때 확인할 점은 무엇인가요?
- 유산균 제품을 고를 때 무엇을 봐야 하나요?
"""
)

st.warning(
    """
이 챗봇은 일반 정보 제공용입니다.  
질병의 진단, 치료, 예방, 처방을 대신하지 않습니다.  
복용 중인 약, 기저질환, 임신·수유, 수술 예정, 알레르기가 있다면 의사 또는 약사와 상담하세요.
"""
)


# =========================
# 8. 세션 상태 초기화
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "안녕하세요. 저는 건강 보조제 정보 챗봇입니다. "
                "성분 정보, 라벨 확인사항, 섭취 시 주의사항을 일반 정보 기준으로 안내해드릴 수 있습니다. "
                "어떤 성분이나 제품이 궁금하신가요?"
            ),
        }
    ]


# =========================
# 9. 기존 대화 출력
# =========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# 10. 사용자 입력 처리
# =========================

if not api_key:
    st.info("왼쪽 사이드바에서 OpenAI API Key를 입력하세요.", icon="🗝️")
else:
    client = OpenAI(api_key=api_key)

    prompt = st.chat_input("예: 오메가3랑 혈압약을 같이 먹어도 되나요?")

    if prompt:
        # 사용자 메시지 저장
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        # 사용자 메시지 출력
        with st.chat_message("user"):
            st.markdown(prompt)

        # 위험도 간단 표시
        detected_risks = classify_risk(prompt, user_profile)

        if detected_risks:
            with st.expander("⚠️ 감지된 주의 항목", expanded=False):
                for risk in detected_risks:
                    st.write(f"- {risk}")

        # API 메시지 구성
        api_messages = make_api_messages(
            user_prompt=prompt,
            profile=user_profile,
            max_history=12,
        )

        # Assistant 응답 생성
        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=api_messages,
                    temperature=0.2,
                    stream=True,
                )

                response = st.write_stream(
                    stream_openai_response(stream)
                )

                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as e:
                error_message = f"""
응답 생성 중 오류가 발생했습니다.

가능한 원인:
1. API Key가 잘못되었거나 만료됨
2. 입력한 모델명을 현재 계정에서 사용할 수 없음
3. 네트워크 문제
4. OpenAI API 사용량 또는 결제 설정 문제

오류 내용:
`{e}`
"""
                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다. API Key와 모델명을 확인해주세요.",
                    }
                )

import streamlit as st
from openai import OpenAI


# =========================
# 1. 페이지 설정
# =========================

st.set_page_config(
    page_title="증상 기반 건강 보조제 챗봇",
    page_icon="💊",
    layout="centered",
)


# =========================
# 2. 시스템 프롬프트
# =========================

SYSTEM_PROMPT = """
너는 한국어로 답변하는 '증상 기반 건강 보조제 정보 챗봇'이다.

너의 역할:
- 사용자가 말한 증상이나 불편감을 바탕으로 일반적인 건강 정보와 생활관리 방향을 설명한다.
- 증상과 관련해 고려해볼 수 있는 비타민, 미네랄, 건강기능식품, 보조제 후보를 제안한다.
- 단, 질병을 진단하거나 치료, 예방, 완치 효과를 단정하지 않는다.
- 보조제를 의약품처럼 설명하지 않는다.
- 복용 중인 약, 기저질환, 임신·수유, 수술 예정, 알레르기, 어린이·고령자 관련 질문은 반드시 의사 또는 약사 상담을 권한다.

반드시 지켜야 할 규칙:
1. 질병을 진단하지 않는다.
2. "이걸 먹으면 낫는다", "치료된다", "예방된다", "약 대신 먹어라"라고 말하지 않는다.
3. 특정 보조제를 질병 치료 목적으로 추천하지 않는다.
4. 복용량은 제품 표시사항, 식약처 인정 내용, 전문가 상담 기준으로 확인하라고 안내한다.
5. 위험 증상은 즉시 의료기관 상담을 우선 안내한다.
6. 약물 병용 질문에는 안전하게 단정하지 말고 의사 또는 약사 상담을 안내한다.
7. 임신·수유, 수술 예정, 만성질환자는 보조제 섭취 전 전문가 상담을 안내한다.
8. 확실하지 않은 내용은 "확인 필요"라고 말한다.
9. 답변은 일반 정보 제공 목적이며 의료 조언이 아님을 분명히 한다.
10. 사용자가 말한 증상과 내부 추천 후보 자료를 연결해서 답하되, 내부 자료에 없는 내용은 과장하지 않는다.

답변 형식:
1. 먼저 사용자가 말한 증상을 짧게 정리한다.
2. 가능한 원인을 단정하지 말고 일반적인 가능성 범위로 설명한다.
3. "고려해볼 수 있는 보조제 후보"를 2~4개 제안한다.
4. 각 보조제마다 다음을 설명한다.
   - 왜 고려할 수 있는지
   - 라벨에서 확인할 것
   - 주의할 사람
5. 마지막에는 병원 또는 약사 상담이 필요한 경우를 안내한다.
"""


# =========================
# 3. 증상별 보조제 추천 후보 DB
# 실제 서비스에서는 식약처, 식품안전나라, NIH ODS 등 공식 자료 기반 DB로 교체 권장
# =========================

SYMPTOM_RECOMMENDATION_DB = {
    "피로/무기력": {
        "keywords": [
            "피곤", "피로", "무기력", "기운이 없어", "힘이 없어", "졸려",
            "컨디션", "몸이 무거", "만성피로", "쉽게 지쳐"
        ],
        "description": "피로감은 수면 부족, 스트레스, 영양 불균형, 운동 부족, 빈혈, 갑상선 문제, 감염, 우울감 등 다양한 원인과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "비타민 B군",
                "why": "에너지 대사와 관련된 비타민군이라 피로감을 느끼는 사람이 많이 찾는 성분입니다.",
                "check": "B1, B2, B6, B12, 나이아신, 판토텐산 함량과 1일 섭취량을 확인하세요.",
                "caution": "고함량 제품은 사람에 따라 속불편, 소변색 변화 등이 있을 수 있습니다."
            },
            {
                "name": "비타민 D",
                "why": "실내 생활이 많거나 햇빛 노출이 적은 사람이 자주 확인하는 영양 성분입니다.",
                "check": "1일 섭취량, IU 또는 μg 단위, 다른 멀티비타민과 중복 여부를 확인하세요.",
                "caution": "신장질환, 고칼슘혈증, 고함량 장기 섭취는 전문가 상담이 필요합니다."
            },
            {
                "name": "마그네슘",
                "why": "근육과 신경 기능, 에너지 대사와 관련된 미네랄입니다.",
                "check": "마그네슘 형태, 함량, 1일 섭취량을 확인하세요.",
                "caution": "신장질환이 있거나 설사가 잦은 사람은 주의가 필요합니다."
            },
            {
                "name": "철분",
                "why": "철 부족이나 빈혈이 있는 경우 피로감과 관련될 수 있으나, 검사 없이 무조건 섭취하는 성분은 아닙니다.",
                "check": "철분 함량, 철 형태, 비타민 C 포함 여부, 위장 불편 가능성을 확인하세요.",
                "caution": "철분은 과다 섭취 위험이 있어 혈액검사나 전문가 상담 후 고려하는 것이 안전합니다."
            }
        ]
    },

    "눈 피로/건조": {
        "keywords": [
            "눈이 피로", "눈 피곤", "눈 건조", "안구건조", "눈 뻑뻑",
            "눈 침침", "시야", "눈이 아파", "눈이 뻐근"
        ],
        "description": "눈 피로와 건조감은 화면 사용, 수면 부족, 건조한 환경, 렌즈 착용, 안과 질환 등과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "루테인/지아잔틴",
                "why": "눈 건강 관련 건강기능식품에서 자주 사용되는 카로티노이드 성분입니다.",
                "check": "루테인 함량, 지아잔틴 포함 여부, 1일 섭취량을 확인하세요.",
                "caution": "눈 질환이 있거나 시야 변화가 있으면 안과 진료가 우선입니다."
            },
            {
                "name": "오메가3",
                "why": "건조감 관리와 관련해 관심을 받는 지방산 성분입니다.",
                "check": "EPA/DHA 함량, 원료, 산패 관리, 1일 섭취량을 확인하세요.",
                "caution": "항응고제, 항혈소판제 복용자나 수술 예정자는 전문가 상담이 필요합니다."
            },
            {
                "name": "아스타잔틴",
                "why": "눈 피로 관련 제품에서 부원료 또는 기능성 원료로 사용되는 경우가 있습니다.",
                "check": "함량, 원료명, 기능성 표시 내용을 확인하세요.",
                "caution": "제품별 인정 내용이 다를 수 있으므로 표시사항 확인이 필요합니다."
            }
        ]
    },

    "수면/긴장": {
        "keywords": [
            "잠이 안", "불면", "수면", "잠을 못", "자주 깨", "긴장",
            "스트레스", "예민", "불안", "잠들기"
        ],
        "description": "수면 문제는 스트레스, 카페인, 생활 리듬, 운동 부족, 우울·불안, 약물, 질환 등 여러 요인과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "마그네슘",
                "why": "근육과 신경 기능과 관련되어 수면 전 긴장감을 느끼는 사람이 많이 찾는 성분입니다.",
                "check": "마그네슘 형태, 함량, 1일 섭취량을 확인하세요.",
                "caution": "신장질환이 있거나 약을 복용 중이면 상담이 필요합니다."
            },
            {
                "name": "L-테아닌",
                "why": "긴장 완화, 스트레스 관리 관련 제품에서 자주 사용되는 아미노산 성분입니다.",
                "check": "L-테아닌 함량, 카페인 포함 여부, 섭취 시점을 확인하세요.",
                "caution": "수면제, 항불안제, 항우울제 등을 복용 중이면 전문가 상담이 필요합니다."
            },
            {
                "name": "비타민 B군",
                "why": "신경계와 에너지 대사에 관여하는 영양소로 스트레스가 많은 사람이 확인해볼 수 있습니다.",
                "check": "B6, B12, 엽산 등의 함량과 1일 섭취량을 확인하세요.",
                "caution": "고함량 제품은 장기 섭취 시 주의가 필요할 수 있습니다."
            }
        ]
    },

    "장 건강/소화": {
        "keywords": [
            "소화", "더부룩", "가스", "복부팽만", "변비", "설사",
            "장", "배변", "속이 불편", "속이 더부룩"
        ],
        "description": "소화 불편은 식습관, 스트레스, 장내 환경, 유당불내증, 과민성대장, 위장질환 등과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "프로바이오틱스",
                "why": "장 건강 관련 건강기능식품에서 가장 흔히 사용되는 유산균 제품군입니다.",
                "check": "균주명, 보장균수, 보관 방법, 섭취 기한을 확인하세요.",
                "caution": "면역저하자, 중증질환자, 중심정맥관 보유자는 전문가 상담이 필요합니다."
            },
            {
                "name": "프리바이오틱스/식이섬유",
                "why": "장내 유익균 환경과 배변 습관 관리에 관심 있는 사람이 고려할 수 있습니다.",
                "check": "식이섬유 종류, 함량, 당류 함량, 물 섭취 필요 여부를 확인하세요.",
                "caution": "과량 섭취 시 가스, 복부팽만이 심해질 수 있습니다."
            },
            {
                "name": "소화효소 제품",
                "why": "식후 더부룩함이 있을 때 일부 사람들이 찾는 제품군입니다.",
                "check": "효소 종류, 원료, 알레르기 유발 원료 여부를 확인하세요.",
                "caution": "지속적인 복통, 체중 감소, 혈변, 검은변이 있으면 병원 진료가 우선입니다."
            }
        ]
    },

    "근육 경련/쥐": {
        "keywords": [
            "쥐가", "근육 경련", "근육통", "다리 저림", "종아리",
            "눈떨림", "떨림", "근육이 뭉쳐"
        ],
        "description": "근육 경련은 수분 부족, 전해질 불균형, 과사용, 운동, 약물, 신경·혈관 문제 등과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "마그네슘",
                "why": "근육과 신경 기능에 관여하는 미네랄로 근육 경련을 말할 때 자주 언급됩니다.",
                "check": "마그네슘 함량, 형태, 1일 섭취량을 확인하세요.",
                "caution": "신장질환자는 전문가 상담 없이 고함량 섭취를 피하는 것이 좋습니다."
            },
            {
                "name": "칼슘 + 비타민 D",
                "why": "뼈와 근육 기능 관련 영양소로 함께 확인해볼 수 있습니다.",
                "check": "칼슘, 비타민D 함량과 중복 섭취 여부를 확인하세요.",
                "caution": "고칼슘혈증, 신장결석 이력이 있으면 상담이 필요합니다."
            },
            {
                "name": "전해질 제품",
                "why": "땀을 많이 흘리거나 운동량이 많을 때 수분·전해질 보충 측면에서 고려할 수 있습니다.",
                "check": "나트륨, 칼륨, 당류 함량을 확인하세요.",
                "caution": "고혈압, 신장질환, 심장질환이 있으면 전해질 제품도 전문가 상담이 필요합니다."
            }
        ]
    },

    "피부/트러블": {
        "keywords": [
            "피부", "트러블", "여드름", "건조", "피부염", "가려움",
            "탄력", "주름", "피부 장벽"
        ],
        "description": "피부 문제는 수면, 스트레스, 호르몬, 식습관, 알레르기, 피부질환, 화장품 자극 등과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "비타민 C",
                "why": "항산화와 콜라겐 형성 관련 영양소로 피부 관련 제품에서 자주 사용됩니다.",
                "check": "비타민C 함량, 산성으로 인한 위장 부담 가능성을 확인하세요.",
                "caution": "위가 예민하거나 신장결석 이력이 있으면 주의가 필요합니다."
            },
            {
                "name": "콜라겐",
                "why": "피부 탄력, 보습 관련 제품에서 많이 사용되는 단백질 유래 성분입니다.",
                "check": "콜라겐 원료, 1일 섭취량, 당류, 부원료를 확인하세요.",
                "caution": "알레르기 유발 원료, 어류·돼지·소 유래 여부를 확인하세요."
            },
            {
                "name": "아연",
                "why": "정상적인 면역 기능과 세포 분열에 관여하는 미네랄입니다.",
                "check": "아연 함량, 멀티비타민과 중복 여부를 확인하세요.",
                "caution": "고함량 장기 섭취는 구리 부족 등 문제가 생길 수 있어 주의가 필요합니다."
            },
            {
                "name": "오메가3",
                "why": "피부 건조감과 염증성 반응 관리에 관심 있는 사람이 확인하는 성분입니다.",
                "check": "EPA/DHA 함량과 원료를 확인하세요.",
                "caution": "항응고제 복용자, 수술 예정자는 전문가 상담이 필요합니다."
            }
        ]
    },

    "면역/감기 잦음": {
        "keywords": [
            "면역", "감기", "자주 아파", "몸살", "목감기", "코감기",
            "염증", "회복이 느려"
        ],
        "description": "면역 관련 불편감은 수면, 영양상태, 스트레스, 운동, 만성질환, 감염 등 다양한 요인과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "비타민 D",
                "why": "정상적인 면역 기능과 관련해 자주 확인하는 영양 성분입니다.",
                "check": "함량, 1일 섭취량, 기존 섭취 제품과 중복 여부를 확인하세요.",
                "caution": "고함량 장기 섭취는 전문가 상담이 필요합니다."
            },
            {
                "name": "아연",
                "why": "정상적인 면역 기능에 관여하는 미네랄입니다.",
                "check": "아연 함량, 멀티비타민 중복 여부를 확인하세요.",
                "caution": "고함량 장기 섭취는 피하는 것이 좋습니다."
            },
            {
                "name": "비타민 C",
                "why": "항산화와 정상적인 면역 기능 관련 제품에서 흔히 사용됩니다.",
                "check": "함량, 산성 여부, 위장 부담 가능성을 확인하세요.",
                "caution": "고함량 섭취 시 속불편, 설사 등이 있을 수 있습니다."
            },
            {
                "name": "프로바이오틱스",
                "why": "장 건강과 면역 균형에 관심 있는 사람이 고려할 수 있는 제품군입니다.",
                "check": "균주명, 보장균수, 보관 방법을 확인하세요.",
                "caution": "면역저하자는 전문가 상담이 필요합니다."
            }
        ]
    },

    "관절/뼈": {
        "keywords": [
            "관절", "무릎", "손목", "어깨", "허리", "뼈", "골다공",
            "관절통", "뻣뻣"
        ],
        "description": "관절과 뼈 불편감은 운동량, 체중, 자세, 염증성 질환, 골밀도, 노화 등과 관련될 수 있습니다.",
        "candidates": [
            {
                "name": "비타민 D + 칼슘",
                "why": "뼈 건강 관련 영양소로 함께 자주 확인됩니다.",
                "check": "비타민D, 칼슘 함량과 1일 섭취량을 확인하세요.",
                "caution": "신장질환, 신장결석, 고칼슘혈증 이력이 있으면 상담이 필요합니다."
            },
            {
                "name": "MSM",
                "why": "관절 건강 제품에서 자주 사용되는 성분입니다.",
                "check": "MSM 함량, 기능성 표시 내용, 1일 섭취량을 확인하세요.",
                "caution": "위장 불편이 있을 수 있으며 약물 복용자는 상담이 좋습니다."
            },
            {
                "name": "글루코사민/콘드로이틴",
                "why": "관절 건강 관련 제품군에서 흔히 보이는 성분입니다.",
                "check": "원료 유래, 함량, 1일 섭취량을 확인하세요.",
                "caution": "갑각류 알레르기, 당뇨, 항응고제 복용자는 전문가 상담이 필요합니다."
            },
            {
                "name": "오메가3",
                "why": "관절 불편감과 관련해 관심을 받는 지방산입니다.",
                "check": "EPA/DHA 함량을 확인하세요.",
                "caution": "항응고제 복용자, 수술 예정자는 상담이 필요합니다."
            }
        ]
    },

    "탈모/모발": {
        "keywords": [
            "탈모", "머리 빠", "모발", "머리카락", "손톱", "손톱이 약해",
            "머리숱", "두피"
        ],
        "description": "탈모와 모발 문제는 유전, 스트레스, 철분 부족, 갑상선, 호르몬, 다이어트, 두피질환 등 원인이 다양합니다.",
        "candidates": [
            {
                "name": "비오틴",
                "why": "모발·손톱 관련 제품에서 많이 사용되는 비타민 B군 성분입니다.",
                "check": "비오틴 함량과 다른 멀티비타민과의 중복 여부를 확인하세요.",
                "caution": "일부 혈액검사 결과에 영향을 줄 수 있어 검사 전 의료진에게 알려야 합니다."
            },
            {
                "name": "아연",
                "why": "세포 분열과 정상적인 면역 기능에 관여하는 미네랄입니다.",
                "check": "아연 함량과 중복 섭취 여부를 확인하세요.",
                "caution": "고함량 장기 섭취는 주의가 필요합니다."
            },
            {
                "name": "철분",
                "why": "철 부족이 확인된 경우 모발 문제와 관련될 수 있으나 검사 없이 무조건 섭취할 성분은 아닙니다.",
                "check": "혈액검사, 철분 함량, 위장 부담 가능성을 확인하세요.",
                "caution": "철분은 과다 섭취 위험이 있어 전문가 상담 후 고려하는 것이 안전합니다."
            },
            {
                "name": "비타민 D",
                "why": "영양상태 확인 차원에서 함께 보는 경우가 있습니다.",
                "check": "함량, 중복 섭취 여부를 확인하세요.",
                "caution": "고함량 장기 섭취는 주의가 필요합니다."
            }
        ]
    }
}


# =========================
# 4. 위험 키워드
# =========================

EMERGENCY_KEYWORDS = [
    "숨이 차", "호흡곤란", "가슴통증", "흉통", "실신", "기절", "의식",
    "얼굴이 부었", "입술이 부었", "목이 부었", "아나필락시스",
    "피를 토", "혈변", "검은변", "심한 복통", "응급", "마비", "말이 어눌"
]

MEDICATION_KEYWORDS = [
    "혈압약", "당뇨약", "고지혈증약", "항응고제", "와파린", "아스피린",
    "항혈소판제", "항우울제", "수면제", "진통제", "항생제", "스테로이드",
    "약 먹고", "약 복용", "복용 중", "같이 먹어", "함께 먹어", "병용"
]

DISEASE_KEYWORDS = [
    "암", "당뇨", "고혈압", "저혈압", "고지혈증", "신장질환", "콩팥",
    "간질환", "간수치", "갑상선", "우울증", "불안장애", "공황장애",
    "심장병", "부정맥", "위염", "역류성식도염", "과민성대장", "통풍",
    "자가면역", "류마티스", "골다공증"
]

PREGNANCY_KEYWORDS = [
    "임신", "임산부", "수유", "모유", "출산", "태아"
]

SURGERY_KEYWORDS = [
    "수술", "시술", "마취", "내시경", "치과수술"
]

CURE_CLAIM_KEYWORDS = [
    "낫게", "낫는", "치료", "완치", "예방", "없애", "고쳐",
    "약 대신", "당뇨에 좋은", "암에 좋은", "고혈압에 좋은"
]


# =========================
# 5. 함수
# =========================

def normalize_text(text: str) -> str:
    return text.lower().replace(" ", "")


def keyword_found(text: str, keywords: list) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(keyword) in normalized for keyword in keywords)


def detect_symptom_categories(user_text: str) -> list:
    """사용자 입력에서 증상 카테고리 감지"""
    detected = []

    for category, data in SYMPTOM_RECOMMENDATION_DB.items():
        if keyword_found(user_text, data["keywords"]):
            detected.append(category)

    return detected


def classify_risk(user_text: str, profile: dict) -> list:
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

    if profile.get("child_or_elderly"):
        risks.append("어린이·고령자 관련 확인 필요")

    if keyword_found(user_text, CURE_CLAIM_KEYWORDS):
        risks.append("질병 치료·예방 표현 주의")

    return risks


def build_profile_context(profile: dict) -> str:
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


def build_symptom_context(categories: list) -> str:
    if not categories:
        return """
감지된 증상 카테고리 없음.

지침:
- 사용자의 증상을 다시 확인하는 질문을 1~2개 포함한다.
- 그래도 일반적으로 많이 확인하는 보조제 후보를 무리하게 추천하지 않는다.
- 수면, 식사, 운동, 스트레스, 병원 상담 필요성을 함께 안내한다.
"""

    blocks = []

    for category in categories:
        data = SYMPTOM_RECOMMENDATION_DB[category]

        candidate_lines = []
        for c in data["candidates"]:
            candidate_lines.append(
                f"""
보조제 후보: {c["name"]}
고려 이유: {c["why"]}
라벨 확인: {c["check"]}
주의사항: {c["caution"]}
""".strip()
            )

        block = f"""
증상 카테고리: {category}
설명: {data["description"]}

추천 후보:
{chr(10).join(candidate_lines)}
"""
        blocks.append(block.strip())

    return "\n\n---\n\n".join(blocks)


def build_risk_context(risks: list) -> str:
    if not risks:
        return "특별한 고위험 신호가 감지되지 않았음. 그래도 일반 정보 제공 원칙을 지킬 것."

    return f"""
감지된 위험 신호:
{", ".join(risks)}

답변 지침:
- 위험 신호를 무시하지 말 것.
- 약물 병용, 질환, 임신·수유, 수술 관련 질문은 안전하게 단정하지 말 것.
- 응급 가능성이 있으면 보조제 추천보다 즉시 의료기관/119/응급실 안내를 우선할 것.
- 치료·예방·완치 효과로 표현하지 말 것.
- 추천은 "고려해볼 수 있는 후보"로만 표현할 것.
"""


def make_api_messages(user_prompt: str, profile: dict, max_history: int = 10) -> list:
    categories = detect_symptom_categories(user_prompt)
    risks = classify_risk(user_prompt, profile)

    profile_context = build_profile_context(profile)
    symptom_context = build_symptom_context(categories)
    risk_context = build_risk_context(risks)

    context_prompt = f"""
아래 정보는 현재 사용자 질문에 대한 참고자료다.

[사용자 상태]
{profile_context}

[감지된 증상 기반 추천 후보]
{symptom_context}

[위험도 분류]
{risk_context}

중요:
- 이 자료는 MVP용 예시 DB다.
- 공식 자료, 제품 표시사항, 전문가 상담이 최종 기준이다.
- 답변에서 보조제를 추천할 때는 "치료제"가 아니라 "고려해볼 수 있는 후보"라고 표현한다.
- 복용량을 단정하지 말고 제품 라벨과 전문가 상담을 확인하라고 말한다.
"""

    recent_messages = st.session_state.messages[-max_history:]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_prompt},
    ]

    messages.extend(
        {"role": m["role"], "content": m["content"]}
        for m in recent_messages
    )

    return messages


def stream_openai_response(stream):
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
        help="테스트용입니다. 실제 배포 시에는 .streamlit/secrets.toml 사용을 권장합니다.",
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
        help="본인 계정에서 사용 가능한 모델명으로 변경할 수 있습니다.",
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
        "이 앱은 증상 기반 건강 보조제 정보 제공용 MVP입니다. "
        "실제 서비스에서는 공식 DB, 전문가 검수, 광고 표현 검토가 필요합니다."
    )


# =========================
# 7. 메인 화면
# =========================

st.title("💊 증상 기반 건강 보조제 챗봇")

st.write(
    """
증상이나 불편감을 입력하면, 일반적인 설명과 함께 고려해볼 수 있는 비타민·미네랄·건강 보조제 후보를 안내합니다.

예시 질문:
- 요즘 너무 피곤하고 기운이 없어요.
- 눈이 뻑뻑하고 침침해요.
- 잠을 잘 못 자고 자주 깨요.
- 장이 더부룩하고 변비가 있어요.
- 다리에 쥐가 자주 나요.
- 피부가 건조하고 트러블이 있어요.
- 머리카락이 많이 빠져요.
"""
)

st.warning(
    """
이 챗봇은 일반 정보 제공용입니다.  
질병의 진단, 치료, 예방, 처방을 대신하지 않습니다.  
복용 중인 약, 기저질환, 임신·수유, 수술 예정, 알레르기가 있다면 보조제 섭취 전 의사 또는 약사와 상담하세요.
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
                "안녕하세요. 증상이나 불편감을 말씀해주시면, "
                "일반적인 설명과 함께 고려해볼 수 있는 비타민·미네랄·건강 보조제 후보를 안내해드리겠습니다. "
                "예: '요즘 너무 피곤해요', '눈이 건조해요', '잠을 잘 못 자요'"
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
# 10. 입력 처리
# =========================

if not api_key:
    st.info("왼쪽 사이드바에서 OpenAI API Key를 입력하세요.", icon="🗝️")
else:
    client = OpenAI(api_key=api_key)

    prompt = st.chat_input("예: 요즘 너무 피곤하고 잠도 잘 못 자요.")

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        detected_categories = detect_symptom_categories(prompt)
        detected_risks = classify_risk(prompt, user_profile)

        if detected_categories:
            with st.expander("🔎 감지된 증상 카테고리", expanded=False):
                for category in detected_categories:
                    st.write(f"- {category}")

        if detected_risks:
            with st.expander("⚠️ 감지된 주의 항목", expanded=False):
                for risk in detected_risks:
                    st.write(f"- {risk}")

        api_messages = make_api_messages(
            user_prompt=prompt,
            profile=user_profile,
            max_history=10,
        )

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

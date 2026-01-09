Developer 메시지 문구를 공식 권장 문장으로 시작
현재 프롬프트 앞에 “You are a model that can do function calling with the following functions”를 넣고, 그 뒤에 도메인 규칙을 붙이는 방식이 가장 정석.
도구 스키마 설명을 한국어(또는 한/영 병기)로 변경
함수 이름은 영어 그대로 두고, description/parameters.description만 한국어로 적으면 한국어 입력 매칭이 좋아지는 경향이 있음.
한국어 few-shot 예시 추가 (키워드 룰 없이)
“현재 온도 알려줘”, “온도 몇 도야?” 같은 질문형을 여러 개 넣어 get_current_temperature로 유도.
“1도/2도 올려줘” 같은 상대 온도는 adjust_temperature로 예시 강화.
파인튜닝(LoRA) 권장
문서상 FunctionGemma는 도메인 파인튜닝을 전제로 설계된 모델.
작은 한국어 AC 도메인 데이터로 LoRA/QLoRA 하면 가장 안정적.
원하면 바로 적용해줄 수 있는 옵션:

developer 메시지 문구 정리 + 도구 설명 한국어화
한국어 few-shot 추가
LoRA 파인튜닝 설계(데이터 스키마/스크립트까지)
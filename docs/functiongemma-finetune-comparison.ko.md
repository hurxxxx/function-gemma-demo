# FunctionGemma 파인튜닝 전/후 비교 리포트 (Demo Commands 기준)

이 리포트는 `docs/demo-commands.ko.md`에 수록된 데모 명령(총 79개)을 기준으로,
베이스 모델과 LoRA 파인튜닝 모델의 실제 추론 결과를 비교한 기록입니다.

## 평가 기준
- **베이스 모델:** `google/functiongemma-270m-it` (어댑터 미적용)
- **파인튜닝 후:** 베이스 + LoRA 어댑터 (`training/output_lora`)
- **평가 세트:** `docs/demo-commands.ko.md` (검증된 데모 명령 모음)
- **비교 방식:** 사용자 의도를 정답 함수 호출(시퀀스+파라미터)으로 정의하고, 모델 출력과의 **정확 일치율**을 측정

## 정확도 정의
- **정확 일치:** 함수 이름/파라미터가 기대값과 완전히 동일해야 함 (순서 포함)
- **앱 이름 정규화:** `Tving`/`TVING`, `YouTube`/`유튜브` 등은 동일 취급
- **수치 정규화:** `30`과 `30.0`은 동일 취급
- **의도 규칙 예시:** “청소기 멈춰”는 `vacuum_stop()`으로 정의

## 실행 정보
- 실행 시각: 2026-01-14T22:36:15+09:00
- 사용 스크립트: `training/quick_infer.py`
- 모델 옵션: `attn_implementation=eager`, `dtype=fp32`, `max_new_tokens=128`
- 출력 파일:
  - 베이스 결과: `docs/eval_base.jsonl`
  - LoRA 결과: `docs/eval_lora.jsonl`
  - 프롬프트 목록: `docs/demo-commands.prompts.ko.txt`

## 평가 세트 요약
- 총 79개 프롬프트
- 범주별 분포
  - 에어컨 12
  - TV / 앱 13
  - 조명 6
  - 커튼 7
  - 환풍기 6
  - 오디오 8
  - 로봇청소기 8
  - 복합 명령 (멀티 기기) 19

## 결과 요약 (사용자 의도 정확도)
- **정확도:** 베이스 10/79 (12.7%) → LoRA 62/79 (78.5%) **(+65.8%p)**
- **파싱 성공률:** 베이스 74/79 (93.7%), LoRA 79/79 (100%)
- **복합 명령 정확도:** 베이스 0/19 (0%), LoRA 9/19 (47.4%)

| 모델 | 정확(%) | 정확/전체 | 파싱 성공 |
| --- | ---: | ---: | ---: |
| 베이스 | 12.7% | 10/79 | 74/79 (93.7%) |
| LoRA | 78.5% | 62/79 | 79/79 (100%) |

## 범주별 정확도

| 범주 | 개수 | 베이스 정확 | LoRA 정확 |
| --- | ---: | ---: | ---: |
| 에어컨 | 12 | 2/12 (16.7%) | 10/12 (83.3%) |
| TV / 앱 | 13 | 2/13 (15.4%) | 11/13 (84.6%) |
| 조명 | 6 | 0/6 (0%) | 6/6 (100%) |
| 커튼 | 7 | 2/7 (28.6%) | 7/7 (100%) |
| 환풍기 | 6 | 2/6 (33.3%) | 5/6 (83.3%) |
| 오디오 | 8 | 0/8 (0%) | 8/8 (100%) |
| 로봇청소기 | 8 | 2/8 (25.0%) | 6/8 (75.0%) |
| 복합 명령 (멀티 기기) | 19 | 0/19 (0%) | 9/19 (47.4%) |

## 베이스 오답 vs LoRA 정답 예시 (발췌)
- “에어컨 꺼줘”  
  - 베이스: `tv_power_off()`  
  - LoRA: `ac_power_off()`
- “에어컨 24도로 맞춰줘”  
  - 베이스: `ac_power_on(mode=ventilation)`  
  - LoRA: `ac_set_temperature(temperature=24)`
- “에어컨 팬 강으로”  
  - 베이스: (빈 출력)  
  - LoRA: `ac_set_fan_speed(speed=high)`
- “TV 9번 채널로”  
  - 베이스: `tv_set_channel()` (채널 누락)  
  - LoRA: `tv_set_channel(channel=9)`
- “조명 켜줘”  
  - 베이스: `light_set_brightness()`, `light_set_color_temp()`  
  - LoRA: `light_power_on()`
- “커튼 30퍼센트로”  
  - 베이스: `curtain_open()`, `ventilation_power_on()`, `ventilation_power_off()`  
  - LoRA: `curtain_set_position(position=30)`
- “환풍기 약으로”  
  - 베이스: `ventilation_power_on()`, `ventilation_power_off()`  
  - LoRA: `ventilation_set_speed(speed=low)`
- “디즈니플러스 실행해줘”  
  - 베이스: (빈 출력)  
  - LoRA: `tv_launch_app(app_name=Disney+)`
- “주방 청소해줘”  
  - 베이스: (빈 출력)  
  - LoRA: `vacuum_clean_zone(zone=kitchen)`

## LoRA 잔여 오답 예시 (발췌)
- “에어컨 모드 난방으로” → `ac_set_mode(mode=ventilation)` (난방 오해)
- “유튜브 켜줘” → `tv_power_on()` (앱 실행 누락)
- “환풍기 중으로” → `ventilation_set_speed(speed=high)` (중↔강 혼동)
- “청소 시작해” → `vacuum_start()` 외 불필요 호출 추가
- “에어컨 24도 맞추고 조명 켜고 밝기 60, 커튼 30퍼센트로” → `light_power_on()` 및 밝기 파라미터 누락

## 참고: 별도 테스트셋에서 확인된 이슈 (데모 명령 외)
`docs/functiongemma-test-report.ko.md`에 기록된 잔여 이슈입니다.
- “거실 청소 시작해줘” → `vacuum_clean_zone(living_room)` 앞 불필요 호출 추가
- “조명 색온도 3000으로” → `light_set_brightness(3000)`으로 오매핑
- “TV 켜고 에어컨 26도, 조명 50%, 커튼 닫아줘” → 불필요 `light_adjust_brightness` 추가
- “청소기 멈춰” → `vacuum_pause`로 해석 (stop vs pause 혼동)
- “영화 볼 준비해줘” → 시나리오 함수 부재로 임의 동작

## 재현 방법
1) 데모 명령 추출
```bash
rg -o -N '^- \"[^\"]+\"$' docs/demo-commands.ko.md | sed 's/^- \"//; s/\"$//' > docs/demo-commands.prompts.ko.txt
```

2) 베이스 모델 추론
```bash
training/venv/bin/python training/quick_infer.py \
  --no_adapter \
  --prompt_file docs/demo-commands.prompts.ko.txt \
  --output_json docs/eval_base.jsonl \
  --quiet \
  --max_new_tokens 128
```

3) LoRA 추론
```bash
training/venv/bin/python training/quick_infer.py \
  --adapter_dir training/output_lora \
  --prompt_file docs/demo-commands.prompts.ko.txt \
  --output_json docs/eval_lora.jsonl \
  --quiet \
  --max_new_tokens 128
```

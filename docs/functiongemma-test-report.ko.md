# FunctionGemma 테스트 리포트 (Home IoT Demo)

English: [functiongemma-test-report.md](functiongemma-test-report.md)

이 문서는 본 프로젝트에서 LoRA 파인튜닝 결과와 기능 테스트 결과를 정리한 이력용 리포트입니다.
유사한 환경에서 재현 테스트를 진행하려는 사용자를 위한 체크리스트도 포함합니다.

## 모델/어댑터 정보
- Base model: `google/functiongemma-270m-it`
- LoRA adapter (repo 내부):
  - `training/output_lora/adapter_model.safetensors`
  - `training/output_lora/adapter_config.json`
- 외부 백업은 선택 사항이며 리포지토리에 보관하지 않습니다.

## 학습 데이터 요약
- 전체 JSONL: `training/data/train_home_ko.jsonl` (3167 lines)
- 학습용: `training/data/train_home_ko.train.jsonl` (2841 lines)
- 검증용: `training/data/train_home_ko.val.jsonl` (326 lines)

## 학습 실행 요약
- Start time: 2026-01-13T17:11:41+09:00
- Epoch: 3
- max_seq_length: 512
- per_device_train_batch_size: 1
- gradient_accumulation_steps: 16
- learning_rate: 1e-4
- attn_implementation: eager
- train_loss: 0.0772939051
- eval_loss: 0.0261247084 (epoch 2.25)
- train_runtime: 6274.1s (~1h44m)
- Logs:
  - `training/logs/finetune_20260113_171141.log`

## 테스트 방법
1) 어댑터 로드
```bash
training/venv/bin/python training/quick_infer.py \
  --adapter_dir training/output_lora \
  --prompt_file docs/functiongemma-test-prompts.txt
```

2) 데모 명령 모음
- `docs/demo-commands.ko.md`

## 결과 요약 (2026-01-13)
테스트 프롬프트 28개 기준 요약입니다.

정상 동작
- 구역 청소(주방/침실), 앱 실행(YouTube/Netflix), 상대 볼륨/온도 조절, 커튼 퍼센트, 환풍기 속도, 오디오 재생 등 대부분 정상.

남은 이슈 (데모에 큰 영향 없음)
1) “거실 청소 시작해줘” → `vacuum_clean_zone(living_room)` 앞에 불필요 호출 추가 (`vacuum_start`, `vacuum_pause`)
2) “조명 색온도 3000으로” → `light_set_brightness(3000)`으로 잘못 매핑
3) “TV 켜고 에어컨 26도, 조명 50%, 커튼 닫아줘” → 불필요 `light_adjust_brightness` 추가
4) “청소기 멈춰” → `vacuum_pause`로 해석 (stop vs pause 혼동)
5) “영화 볼 준비해줘” → 시나리오 함수가 없어 임의 동작 (TV on + 채널 1)

## 데모 권장 프롬프트
아래 파일의 명령어는 확인된 정상 동작 중심으로 구성:
- `docs/demo-commands.ko.md`

## 관련 문서
- demo-commands.ko.md
- functiongemma-test-prompts.txt
- fine-tuning.ko.md

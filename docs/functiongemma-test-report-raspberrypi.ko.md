# FunctionGemma 테스트 리포트 (라즈베리파이)

English: [functiongemma-test-report-raspberrypi.md](functiongemma-test-report-raspberrypi.md)

**Date:** 2026-01-14  
**Platform:** Raspberry Pi (Linux 6.8.0-1044-raspi, ARM64)  
**Model:** google/functiongemma-270m-it  

---

## 1. 요약

이 문서는 라즈베리파이 환경에서 FunctionGemma 모델의 다운로드, 설치, 성능 테스트 결과를 정리합니다. 모델은 정상 로드 및 기본 함수 호출 추론이 가능했지만, ARM CPU 환경에서 성능 한계가 크게 나타났습니다.

| 항목 | 상태 |
|------|------|
| 모델 다운로드 | ✅ 성공 |
| 모델 로드 | ✅ 성공 |
| 기본 추론 | ✅ 동작 |
| 복합 명령 | ⚠️ 파인튜닝 필요 |
| 성능 | ❌ 매우 느림(약 2분/쿼리) |

---

## 2. 환경 구성

### 2.1 하드웨어 사양
- **기기:** Raspberry Pi
- **OS:** Linux 6.8.0-1044-raspi
- **아키텍처:** ARM64
- **연산:** CPU 전용 (GPU 없음)

### 2.2 소프트웨어 스택
- **Python:** 3.12
- **Transformers:** 4.57.3
- **PyTorch:** CPU-only 빌드
- **정밀도:** float32

### 2.3 모델 정보
| 항목 | 값 |
|------|----|
| Model ID | `google/functiongemma-270m-it` |
| 파라미터 | 270M |
| 아키텍처 | Gemma 3 (gemma3_text) |
| 최대 컨텍스트 | 32K tokens |
| 라이선스 | Gated (HF 승인 필요) |

---

## 3. 다운로드 및 설치

### 3.1 진행 과정
1. `.env`에 HuggingFace 토큰 설정
2. `AutoProcessor.from_pretrained()`로 프로세서 로드
3. `AutoModelForCausalLM.from_pretrained()`로 모델 로드
4. 모델 캐시는 `~/.cache/huggingface/`에 저장

### 3.2 결과
| 구성요소 | 상태 | 시간 |
|----------|------|------|
| 프로세서 | ✅ 로드 | ~2s |
| 모델 가중치 | ✅ 다운로드 | ~20s |
| 함수 스키마 | ✅ 37개 로드 | <1s |

---

## 4. 추론 테스트

### 4.1 테스트 구성
```python
SYSTEM_PROMPT = """
You are a model that can do function calling with the following functions.
너는 스마트홈 IoT 기기들을 제어하는 모델이다.
사용자 지시를 해석해서 하나 이상의 함수 호출만 반환하라.
"""

Generation Parameters:
- max_new_tokens: 128
- do_sample: False
- device: CPU
- dtype: float32
```

### 4.2 테스트 케이스 및 결과

#### 테스트 1: 단순 명령 (에어컨 켜기)
| 항목 | 값 |
|------|----|
| 입력 | "에어컨 켜줘" |
| 기대 | `ac_power_on()` |
| 실제 | `ac_power_on()` |
| 상태 | ✅ **PASS** |
| 시간 | 126.22s |
| 토큰 | 11 |

#### 테스트 2: 파라미터 포함 명령 (TV 채널)
| 항목 | 값 |
|------|----|
| 입력 | "TV 9번 채널로" |
| 기대 | `tv_set_channel{channel:9}` |
| 실제 | `tv_set_channel{channel:9}` |
| 상태 | ✅ **PASS** |
| 시간 | 143.06s |
| 토큰 | 15 |

#### 테스트 3: 복합 명령 (다중 동작)
| 항목 | 값 |
|------|----|
| 입력 | "TV 켜고 조명 꺼줘" |
| 기대 | `tv_power_on()` + `light_power_off()` |
| 실제 | `tv_set_mode{mode:ventilation}` |
| 상태 | ❌ **FAIL** |
| 시간 | 131.16s |
| 토큰 | 18 |

### 4.3 요약 통계
| 지표 | 값 |
|------|----|
| 테스트 수 | 3 |
| 통과 | 2 (66.7%) |
| 실패 | 1 (33.3%) |
| 평균 추론 시간 | **133.48s** |
| 최소 시간 | 126.22s |
| 최대 시간 | 143.06s |
| 토큰 속도 | ~0.1 tok/s |

---

## 5. 성능 분석

### 5.1 시간 요약
```
Model Load:     21.58s
Inference Avg: 133.48s (~2.2 minutes per query)
```

### 5.2 병목 요인

| 요인 | 영향 | 상세 |
|------|------|------|
| ARM CPU | 높음 | x86용 SIMD/AVX 최적화 부재 |
| Float32 | 중간 | 양자화 미적용 |
| GPU 없음 | 치명적 | CPU-only는 10~100배 느림 |
| 메모리 | 낮음 | 모델이 RAM (~1GB)에 적재 가능 |

### 5.3 비교 (추정)
| 플랫폼 | 예상 시간 |
|--------|-----------|
| Raspberry Pi (현재) | ~130s |
| x86 CPU (현대) | ~10-20s |
| NVIDIA GPU (RTX 3060) | ~1-2s |
| Apple M1/M2 | ~3-5s |

---

## 6. 기능 분석

### 6.1 정상 동작 기능
- ✅ 단일 함수 호출
- ✅ 숫자 파라미터 추출
- ✅ 한국어 입력 처리
- ✅ FunctionGemma 출력 파싱

### 6.2 확인된 이슈

#### 이슈 1: 복합 명령 실패
- **설명:** 다중 동작 명령이 단일 함수로 잘못 출력됨
- **원인:** 멀티턴/복합 명령에 대한 파인튜닝 부족
- **해결:** LoRA 파인튜닝 적용 (`docs/functiongemma-finetune.ko.md`)

#### 이슈 2: 느린 추론 속도
- **설명:** 평균 2분대 추론은 실사용에 부적합
- **원인:** ARM CPU 단독 추론
- **대응:** 
  1. INT8/INT4 양자화
  2. ONNX Runtime 최적화
  3. 엣지 가속기 사용 (Jetson, Coral TPU)

---

## 7. 권장사항

### 7.1 실서비스 운영
1. **라즈베리파이 실시간 추론은 비권장**
2. 엣지 AI 가속기 고려:
   - NVIDIA Jetson Nano/Orin
   - Google Coral TPU
   - Intel Neural Compute Stick

### 7.2 개발/테스트 목적
1. **INT8 양자화**로 속도/용량 개선
2. **ONNX Runtime** 최적화 적용
3. **캐싱**으로 반복 호출 비용 절감

### 7.3 정확도 개선
1. **LoRA 파인튜닝**으로 복합 명령 개선
2. 시스템 프롬프트 강화
3. 도메인 특화 데이터 추가

---

## 8. 결론

FunctionGemma 270M-IT는 라즈베리파이에서도 기본적인 함수 호출 추론이 가능합니다. 그러나 다음 두 가지 한계가 확인되었습니다:

1. **성능:** 추론 시간이 너무 느림 (~2분/쿼리)
2. **정확도:** 복합 명령에서 실패 발생

실제 스마트홈 서비스에는 하드웨어 가속 또는 클라우드 추론을 권장합니다.

---

## 부록 A: Raw Test Output

```
============================================================
FunctionGemma 추론 테스트
============================================================
[1/3] 모델 로드 중...
✓ 모델 로드 완료

[2/3] 함수 스키마 로드 중...
✓ 37개 함수 스키마 로드됨

[3/3] 추론 테스트...
------------------------------------------------------------
테스트 1: "에어컨 켜줘"
  → ac_power_on()
  Raw: <start_function_call>call:ac_power_on{}<end_function_call>...

테스트 2: "TV 9번 채널로"
  → tv_set_channel(channel:9)
  Raw: <start_function_call>call:tv_set_channel{channel:9}<end_function_call>...

테스트 3: "TV 켜고 조명 꺼줘"
  → tv_set_mode(mode:<escape>ventilation<escape>)
  Raw: <start_function_call>call:tv_set_mode{mode:<escape>ventilation<escape>}...

============================================================
테스트 완료!
============================================================
```

## 부록 B: Timing Data

```
==================================================
Inference Timing Results
==================================================
"에어컨 켜줘"
  Time: 126.22s | Tokens: 11 | Speed: 0.1 tok/s

"TV 9번 채널로"
  Time: 143.06s | Tokens: 15 | Speed: 0.1 tok/s

"TV 켜고 조명 꺼줘"
  Time: 131.16s | Tokens: 18 | Speed: 0.1 tok/s

==================================================
Average inference time: 133.48s
Min: 126.22s | Max: 143.06s
==================================================
```

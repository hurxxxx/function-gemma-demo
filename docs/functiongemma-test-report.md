# FunctionGemma Test Report

**Date:** 2026-01-14  
**Platform:** Raspberry Pi (Linux 6.8.0-1044-raspi, ARM64)  
**Model:** google/functiongemma-270m-it  

---

## 1. Executive Summary

This report documents the download, installation, and performance testing of the FunctionGemma model on a Raspberry Pi platform. The model successfully loads and performs basic function calling inference, but exhibits significant performance limitations on ARM CPU hardware.

| Category | Status |
|----------|--------|
| Model Download | ✅ Success |
| Model Loading | ✅ Success |
| Basic Inference | ✅ Working |
| Compound Commands | ⚠️ Requires Fine-tuning |
| Performance | ❌ Very Slow (~2 min/query) |

---

## 2. Environment Configuration

### 2.1 Hardware Specifications
- **Device:** Raspberry Pi
- **OS:** Linux 6.8.0-1044-raspi
- **Architecture:** ARM64
- **Compute:** CPU only (no GPU)

### 2.2 Software Stack
- **Python:** 3.12
- **Transformers:** 4.57.3
- **PyTorch:** CPU-only build
- **Precision:** float32

### 2.3 Model Details
| Property | Value |
|----------|-------|
| Model ID | `google/functiongemma-270m-it` |
| Parameters | 270M |
| Architecture | Gemma 3 (gemma3_text) |
| Max Context | 32K tokens |
| License | Gated (requires HF approval) |

---

## 3. Download & Installation

### 3.1 Process
1. Configured HuggingFace token in `.env`
2. Loaded processor via `AutoProcessor.from_pretrained()`
3. Loaded model via `AutoModelForCausalLM.from_pretrained()`
4. Model cached to `~/.cache/huggingface/`

### 3.2 Results
| Component | Status | Time |
|-----------|--------|------|
| Processor | ✅ Loaded | ~2s |
| Model Weights | ✅ Downloaded | ~20s |
| Function Schemas | ✅ 37 loaded | <1s |

---

## 4. Inference Testing

### 4.1 Test Configuration
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

### 4.2 Test Cases & Results

#### Test 1: Simple Command (AC Power On)
| Field | Value |
|-------|-------|
| Input | "에어컨 켜줘" (Turn on AC) |
| Expected | `ac_power_on()` |
| Actual | `ac_power_on()` |
| Status | ✅ **PASS** |
| Time | 126.22s |
| Tokens | 11 |

#### Test 2: Command with Parameter (TV Channel)
| Field | Value |
|-------|-------|
| Input | "TV 9번 채널로" (TV to channel 9) |
| Expected | `tv_set_channel{channel:9}` |
| Actual | `tv_set_channel{channel:9}` |
| Status | ✅ **PASS** |
| Time | 143.06s |
| Tokens | 15 |

#### Test 3: Compound Command (Multiple Actions)
| Field | Value |
|-------|-------|
| Input | "TV 켜고 조명 꺼줘" (Turn on TV and turn off lights) |
| Expected | `tv_power_on()` + `light_power_off()` |
| Actual | `tv_set_mode{mode:ventilation}` |
| Status | ❌ **FAIL** |
| Time | 131.16s |
| Tokens | 18 |

### 4.3 Summary Statistics
| Metric | Value |
|--------|-------|
| Total Tests | 3 |
| Passed | 2 (66.7%) |
| Failed | 1 (33.3%) |
| Avg Inference Time | **133.48s** |
| Min Time | 126.22s |
| Max Time | 143.06s |
| Token Speed | ~0.1 tok/s |

---

## 5. Performance Analysis

### 5.1 Timing Breakdown
```
Model Load:     21.58s
Inference Avg: 133.48s (~2.2 minutes per query)
```

### 5.2 Performance Bottlenecks

| Factor | Impact | Details |
|--------|--------|---------|
| ARM CPU | High | No SIMD/AVX optimization for x86 |
| Float32 | Medium | No quantization applied |
| No GPU | Critical | CPU-only inference is 10-100x slower |
| Memory | Low | Model fits in RAM (~1GB) |

### 5.3 Comparison (Estimated)
| Platform | Expected Time |
|----------|---------------|
| Raspberry Pi (current) | ~130s |
| x86 CPU (modern) | ~10-20s |
| NVIDIA GPU (RTX 3060) | ~1-2s |
| Apple M1/M2 | ~3-5s |

---

## 6. Functional Analysis

### 6.1 Working Features
- ✅ Single function calls
- ✅ Parameter extraction (numeric)
- ✅ Korean language input processing
- ✅ FunctionGemma output format parsing

### 6.2 Issues Identified

#### Issue 1: Compound Command Failure
- **Description:** Multi-action commands produce incorrect single function call
- **Root Cause:** Base model not fine-tuned for multi-turn scenarios
- **Solution:** Apply LoRA fine-tuning (see `docs/functiongemma-finetune.md`)

#### Issue 2: Slow Inference
- **Description:** ~2 minutes per inference is impractical for real-time use
- **Root Cause:** CPU-only inference on ARM platform
- **Solutions:**
  1. INT8/INT4 quantization
  2. ONNX Runtime optimization
  3. Use edge-optimized hardware (Jetson, Coral TPU)

---

## 7. Recommendations

### 7.1 For Production Deployment
1. **Do NOT use Raspberry Pi** for real-time inference
2. Consider edge AI accelerators:
   - NVIDIA Jetson Nano/Orin
   - Google Coral TPU
   - Intel Neural Compute Stick

### 7.2 For Development/Testing
1. Apply **INT8 quantization** to reduce model size and improve speed
2. Use **ONNX Runtime** for optimized CPU inference
3. Implement **caching** for repeated queries

### 7.3 For Accuracy Improvement
1. Apply **LoRA fine-tuning** for multi-turn commands
2. Enhance system prompt with more examples
3. Add domain-specific training data

---

## 8. Conclusion

FunctionGemma 270M-IT successfully runs on Raspberry Pi for basic function calling tasks. However, the current configuration has two major limitations:

1. **Performance:** ~2 minutes per inference is too slow for practical use
2. **Accuracy:** Compound commands fail without fine-tuning

For a production smart home system, hardware acceleration or cloud inference is strongly recommended.

---

## Appendix A: Raw Test Output

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

## Appendix B: Timing Data

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

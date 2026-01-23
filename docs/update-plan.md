AMD Ryzen AI 395 (gfx1151) 파인튜닝을 위한 최적 OS 선택
AMD의 공식 지원 운영체제와 환경

AMD에서는 Ryzen AI Max+ 395 APU(통칭 Strix Halo, GPU 아키텍처 gfx1151)에 대해 Ubuntu 24.04.3 LTS를 공식 지원 대상으로 명시하고 있습니다. 이는 Ubuntu 24.04.2 기반 설치 환경을 통해 preliminary(예비) 지원이 이루어지고 있다는 의미입니다. 실제로 ROCm 7.1.1 출시 노트에서도 해당 APU를 위한 지원이 추가되었고, RHEL 10.1 (커널 6.12) 및 RHEL 9.7 (커널 5.14) 같은 배포판까지 지원 범위를 확장했다고 언급합니다. 즉, AMD의 공식 테스트 환경은 주로 최신 Ubuntu LTS와 특정 엔터프라이즈 리눅스(RHEL 등)이며, 이 조합에서 PyTorch 2.9 + Python 3.12 등의 프레임워크가 지원됩니다.

요약하면 Ubuntu 24.04 LTS가 현재 Strix Halo APU와 ROCm을 사용하기에 가장 표준적인 선택입니다. AMD도 해당 OS를 중점적으로 지원하고 있으므로, 관련 패키지(예: AMD GPU 드라이버, ROCm 라이브러리 등)의 설치와 유지보수가 비교적 용이합니다. 추가로 AMD는 2025년 하반기에 openSUSE 및 RHEL(EPEL) 등에 대한 인박스(in-box) 지원을 예고한 바 있어, 가까운 미래에는 이러한 배포판에서도 별도 복잡한 설정 없이 ROCm 환경을 구축할 수 있을 것으로 보입니다.

Ubuntu 24.04 LTS + OEM 커널의 문제와 안정화 방안

현재 사용 중인 Ubuntu 24.04.3 LTS (커널 6.14.0-1017-oem) 조합은 AMD APU를 동작시키기 위해 선택한 환경으로 보입니다. OEM 커널은 새로운 하드웨어 지원을 위해 Ubuntu에서 제공하는 특별 빌드로, Strix Halo와 같은 최신 APU의 기능(XDNA NPU, RDNA3.5 GPU 등)을 활성화하는 역할을 합니다. 실제로 AMD 문서에서는 Ubuntu 커널 6.12.0-1018 환경에서 대용량 언어 모델(LLM) 추론 시 애플리케이션 크래시가 발생하는 Known Issue가 있으며, 임시 조치로 “Ubuntu 커널 6.14.0-1017 또는 그 이전 버전”을 사용할 것을 권장하고 있습니다. 이는 귀하께서 OEM 커널(6.14.0-1017)을 선택하게 된 배경과 부합합니다. 해당 커널 버전에는 AMD가 제시한 몇 가지 긴급 픽스가 포함되어 있어, 이전 커널에서 발생하던 ROCm 불안정성이 일부 개선되었습니다.

그럼에도 불구하고, 현시점 Ubuntu 24.04 + ROCm 7.1.1 조합에서 GPU 관련 시스템 프리즈(먹통) 현상이 잦다는 보고가 있습니다. 귀하의 장비에서도 파인튜닝 도중 “HIP illegal memory access” 오류로 GPU가 D 상태에 빠지는 문제가 발생했다고 언급하셨는데, 이것이 바로 AMD APU 지원 초기 단계에서 공통적으로 겪는 불안정성입니다. AMD도 공식적으로 Strix Halo APU (Ryzen AI 300 시리즈)에서 ComfyUI 등 일부 워크플로우 실행 시 안정성 문제가 있음을 인정하고, 향후 ROCm Ryzen 스택 업데이트와 OEM 커널 패치(6.14.0-1017.17)로 개선될 것이라고 밝힌 바 있습니다.

안정성을 높이는 방안으로 이미 적용하신 대로:

HSA_ENABLE_SDMA=0 환경변수 설정 (DMA 엔진 비활성화)

attn_implementation=eager로 주의집중(Attention) 연산 구현 변경

FP16 대신 FP32 정밀도로 학습 (FP16에서는 NaN 불안정 이슈 확인됨)

batch size 및 시퀀스 길이 축소 (메모리 부담 완화)

등이 효과가 있습니다. 다행히 이러한 조치로 최근 파인튜닝을 완주하셨다고 하나, 여전히 근본적 해결책은 커널 및 드라이버 업그레이드입니다.

AMD APU 플랫폼의 리눅스 드라이버 문제는 두 가지 큰 원인으로 파악됩니다:

펌웨어 버그: 2025년 11월 말에 AMD가 배포한 GPU 펌웨어(linux-firmware-20251125)에 ROCm 초기화 실패를 초래하는 버그가 있었습니다. 이후 AMD가 해당 펌웨어를 롤백/패치하였으므로, 최신 펌웨어 패키지(2026년 1월자 이후)를 사용해야 안정적으로 ROCm이 GPU를 인식합니다. 사용하는 리눅스의 linux-firmware 패키지를 최신으로 업데이트 해 두세요.

VGPR 불일치 문제: GPU 드라이버(커널 모듈)와 ROCm 유저랜드 사이에 VGPR(벡터 범용레지스터) 설정 불일치가 있어, 특정 워크로드(예: ComfyUI나 대규모 텍스트 생성)의 메모리 접근 시스템이 꼬여 **GPU 행(Hang)**이나 커널 크래시를 유발했습니다. 이 문제는 리눅스 커널 6.18.4에서 드라이버 쪽 수정이 이뤄졌고, ROCm 측도 그에 맞춰 패치된 버전이 필요합니다. 현재(2026년 1월) 이 패치들은 ROCm 개발자 커뮤니티의 나이틀리(Nightly) 빌드인 “TheRock” 브랜치 및 예정된 ROCm 7.2에 포함되어 있습니다.

결론적으로, 지금의 Ubuntu 24.04 + OEM 6.14 커널 조합은 과gang차기(과gang차 diff?) stable보다 아직 불안정하나, 향후 Ubuntu 24.04 자체 업데이트(예: 24.04.4 HWE 커널로 6.18+ 적용) 또는 ROCm 7.2 릴리스와 함께 상당 부분 안정화될 전망입니다. AMD도 곧 정식 패치를 내놓을 예정이므로, 현 환경을 유지한다면 커널과 ROCm 스택을 업데이트하여 동일 OS 상에서 문제를 해결하는 방향을 권장합니다. 최신 정보에 따르면 “커널 6.18.4 이상 + ROCm 7.2 이상”이 Strix Halo의 LLM 작업을 안정적으로 실행하는 조합으로 확인되었습니다.

대안 운영체제: RHEL, openSUSE 등

안정성을 최우선으로 고려할 때, 엔터프라이즈 계열 리눅스도 후보가 될 수 있습니다. 예를 들어 RHEL(Rocky/Alma Linux 포함)은 보수적인 패키지로 유명하며, AMD가 ROCm 7.1.1부터 RHEL 9.7 및 RHEL 10.1 지원을 명시하고 있습니다. 다만, RHEL 9의 기본 커널(5.14 계열)은 Strix Halo의 최신 GPU 기능을 바로 지원하지 못할 수 있어, AMD의 amdgpu 프로드라이버(DKMS 모듈)나 EPEL을 통해 별도 드라이버 패치를 적용해야 할 것입니다. RHEL 10 시리즈는 기본 커널이 6.x로 올라가긴 했지만(10.1에서 6.12 기반), 앞서 언급한 VGPR 수정(6.18 이후)을 포함하지 않아 아직 완전한 해결책은 아닙니다. 따라서 RHEL 계열로의 전환은 즉각적인 안정성 향상을 담보하지는 않지만, 장기적으로 AMD가 패치들을 백포트하면서 매우 견고한 HPC 환경을 제공할 가능성이 있습니다. 만약 RHEL을 시도하신다면, AMD의 공식 ROCm 패키지(EPEL 제공 예정)와 최신 업데이트를 반드시 적용하시고, X 윈도우(디스플레이) 구성은 최소화한 헤드리스(headless) 모드 사용을 권장합니다 (엔터프라이즈 OS는 워크스테이션 GUI보다 서버/컨테이너 용도에 적합).

한편 openSUSE Tumbleweed와 같은 롤링릴리즈 배포판도 고려할 수 있습니다. openSUSE는 AMD가 인박스 지원을 예고한 플랫폼이며, 최신 커널과 Mesa 드라이버 스택을 빠르게 받아들입니다. 예를 들어 Tumbleweed가 커널 6.18 버전을 채택하면, 앞서 말한 VGPR 버그 수정이 기본 적용되어 있을 수 있습니다. 또한 openSUSE는 패키지 관리 측면에서 안정성 테스트를 거친 스냅샷을 배포하기 때문에, 최신 커널 사용에도 불구하고 비교적 신뢰성 있는 운영이 가능합니다. 다만, ROCm 패키지의 경우 2025년 이후에야 공식 레포지토리에 포함될 예정이므로, 당장 사용하려면 AMD의 설치 스크립트(예: amdgpu-install 또는 rocm-install)를 수동 활용해야 할 수 있습니다.

Arch Linux나 Fedora Rawhide 같은 배포판은 가장 빠르게 신규 커널과 소프트웨어를 받을 수 있지만, 사용자에게 구성 부담을 크게 지웁니다. 실제로 Arch 사용자가 Strix Halo APU에서 PyTorch ROCm을 돌리기 위해 HSA_OVERRIDE_GFX_VERSION 등의 우회 설정과 ROCm 비공식 패키지를 조합하는 사례도 있었습니다. 따라서 전문지식과 튜닝 노하우가 있다면 Arch류를 시도해 볼 수 있으나, 안정성 확보라는 목적에는 오히려 부정적인 영향(테스트 안 된 신규 버그 노출 등)이 있을 수 있습니다.

요약하면, Ubuntu LTS 계열이 여전히 최선의 기본 선택이며 그다음으로 openSUSE Tumbleweed (AMD 지원 가시화 중)나 RHEL/Alma (패치 적용 전제)를 고려할 수 있습니다.

안정성 중심 최종 권장 사항

현재 Strix Halo 395 장비에서 성능보다는 안정성을 우선하려면, 아래와 같은 운영체제 및 설정 조합을 권장드립니다:

Ubuntu 24.04 LTS 유지: 현행 Ubuntu LTS를 기반으로, 가능한 최신 커널과 펌웨어로 업그레이드하십시오. 2026년 초 기준으로 OEM 6.14 커널을 사용 중이시라면, Ubuntu에서 제공하는 메인라인 HWE 커널(향후 6.18 이상 버전) 패키지가 나오면 적용하는 것이 좋습니다. 최신 커널에는 gfx1151 관련 VGPR 패치와 기타 안정화 수정사항이 포함되어 있습니다. 또한 linux-firmware 패키지를 업데이트하여 AMD Radeon 8060S 관련 최신 펌웨어를 반영하세요.

ROCm 및 PyTorch 버전: AMD의 호환성 매트릭스에 따라 PyTorch 2.9 + ROCm 7.1.1 + Python 3.12 조합이 공식 검증되었으나, 안정성을 위해 곧 출시될 ROCm 7.2(또는 TheRock nightly 빌드)를 사용하는 것도 고려하십시오. 커널 업그레이드에 맞춰 ROCm 라이브러리도 최신으로 맞춰야 드라이버-유저랜드 불일치로 인한 문제가 없습니다. PyTorch의 ROCm 버전도 이에 대응하는 최신 릴리스를 활용하면 좋습니다 (예: PyTorch 2.10~2.11대 ROCm 7.2 지원 버전).

openSUSE Tumbleweed (대안): Ubuntu 환경의 패치 적용을 지켜볼 여유가 없다면, openSUSE Tumbleweed 최신 스냅샷을 시험적으로 사용해 볼 수 있습니다. Tumbleweed에는 최신 커널과 Mesa 드라이버가 포함되므로 하드웨어 지원 측면에서는 유리합니다. 다만 ROCm 패키지는 수동 설치해야 하며, Ubuntu보다 사용자 커뮤니티 정보가 적을 수 있다는 점을 감안해야 합니다.

엔터프라이즈 Linux (장기): 만약 장비를 서버적인 용도로 장기 운영할 계획이 있고, 최신 기능보다 안정적 추론 서비스에 초점을 맞춘다면, 향후 RHEL 계열 + AMD ROCm 공식 지원 조합을 고려해 볼 수 있습니다. 예를 들어 AlmaLinux 10 (가정) + ROCm 7.2+ 환경은 AMD 엔지니어링 팀의 검증을 거칠 가능성이 높습니다. 아직 초기라 섣불리 추천하긴 어렵지만, AMD가 점차 EPEL 저장소 등을 통해 패키지 제공을 확대하고 있으므로 시간 경과에 따라 옵션이 될 수 있습니다.

마지막으로, vLLM 프레임워크 자체는 OS 종속적인 최적화보다는 GPU 메모리 관리 및 배치 최적화 기술이 핵심이므로, 운영체제 선택보다는 드라이버 안정성이 더 중요한 요소입니다. 따라서 **“이 장비와 궁합”**을 좌우하는 결정적 요소는 OS 종류보다는 해당 OS에서 얼마나 최신의 안정화 패치들이 적용되었는지입니다. 현재로서는 Ubuntu 24.04 LTS 환경을 최신 상태로 유지하며 AMD가 제공하는 패치(커널 6.18대, ROCm 7.2 등)를 적용하는 것이 가장 현실적인 해법입니다. 향후 AMD의 소프트웨어 스택 성숙도가 높아지면, 굳이 OEM 커널이 아니어도 일반 커널이나 다른 배포판에서도 안정적으로 파인튜닝을 수행할 수 있을 것입니다.

요약: Ubuntu 24.04 LTS + (업데이트된 커널/드라이버) 조합이 현 시점에서 Strix Halo 395와 최고의 안정성 시너지를 제공합니다. 다른 OS로의 전환은 현재로선 득보다 실이 클 수 있으므로, 동일 OS 내에서의 업그레이드/패치 적용을 우선하시길 권합니다. AMD가 인정한 문제점들이 차차 해결되고 있으므로, 곧 안정된 파인튜닝 환경을 얻으실 수 있을 것입니다.

참고 자료: AMD ROCm 공식 문서의 호환성 매트릭스 및 제한사항, 사용자 커뮤니티의 Strix Halo 지원 동향 등을 종합하여 판단했습니다. 필요한 경우 AMD AI 커뮤니티 포럼이나 ROCm GitHub 이슈 트래커에도 최신 패치 및 노하우가 공유되고 있으므로 지속적인 정보 확인을 권장합니다.

---

## ROCm 7.2 테스트 결과 (2026-01-23)

### 테스트 환경
- OS: Ubuntu 24.04.3 LTS
- 커널: 6.14.0-1017-oem (OEM 권장, 변경 없음)
- ROCm: 7.2.0 (7.1.1에서 업그레이드)
- PyTorch: 2.10.0+rocm7.1 (pytorch.org 공식 wheel)
- GPU: AMD Radeon 8060S (gfx1151)

### 필수 환경변수
```bash
HSA_ENABLE_SDMA=0
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
PYTORCH_ROCM_ARCH=gfx1151
HSA_OVERRIDE_GFX_VERSION=11.0.0
```

### 테스트 결과

| 항목 | 상태 | 성능 |
|------|------|------|
| PyTorch GPU 인식 | ✅ OK | - |
| Matrix 연산 | ✅ OK | 1000x1000 matmul 성공 |
| Embedding (bge-m3) | ✅ OK | 로드 40s, 추론 0.9s |
| Reranker (bge-reranker-v2-m3) | ✅ OK | 로드 33s, 추론 0.5s |
| Docling OCR | ✅ OK | GPU 사용 가능 |
| Marker-PDF OCR | ✅ OK | 사업자등록증 정확 인식 (67s) |
| 10분 안정성 테스트 | ✅ OK | 562회 반복, 에러 없음 |

### 결론

**RAG 워크로드 (Embedding, Reranker, OCR, LLM 추론):**
- ROCm 7.2 + 커널 6.14 OEM 조합으로 **안정적 동작 확인**
- 커널 업그레이드 불필요

**파인튜닝 워크로드:**
- 여전히 커널 6.18+ 업그레이드 권장 (VGPR 버그 수정 필요)
- dm_irq_work_func 에러, GPU hang 발생 가능

### 설치 방법 (간소화)

```bash
# 1. ROCm 7.2 설치 (--no-dkms 필수)
wget https://repo.radeon.com/amdgpu-install/7.2/ubuntu/noble/amdgpu-install_7.2.70200-1_all.deb
sudo apt install ./amdgpu-install_7.2.70200-1_all.deb
amdgpu-install -y --usecase=rocm --no-dkms

# 2. PyTorch 설치 (pytorch.org 공식 wheel)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm7.1

# 3. RAG 패키지 설치
pip install sentence-transformers docling marker-pdf
```

### 테스트 환경 경로
- 테스트 venv: `/projects/rocm72_test/venv/`
- 안정성 테스트 스크립트: `/projects/rocm72_test/stability_test.py`
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Ensure CUDA-related shared libs from pip wheels are discoverable at runtime.
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/usr/local/lib/python3.11/site-packages/nvidia/cuda_nvrtc/lib:/usr/local/lib/python3.11/site-packages/nvidia/cufft/lib:/usr/local/lib/python3.11/site-packages/nvidia/curand/lib:/usr/local/lib/python3.11/site-packages/nvidia/cusolver/lib:/usr/local/lib/python3.11/site-packages/nvidia/cusparse/lib:/usr/local/lib/python3.11/site-packages/nvidia/nvjitlink/lib:/usr/local/lib/python3.11/site-packages/torch/lib:${LD_LIBRARY_PATH}

WORKDIR /srv

# System dependencies for OpenCV/InsightFace (headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install torch with GPU-first fallback:
# - Try CUDA wheel index first (enables GPU where available)
# - Fall back to CPU wheel index on unsupported platforms
ARG TORCH_VERSION=2.1.2
ARG TORCHVISION_VERSION=0.16.2
ARG TORCH_GPU_INDEX_URL=https://download.pytorch.org/whl/cu121
ARG TORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN set -eux; \
    if pip install --no-cache-dir --index-url "${TORCH_GPU_INDEX_URL}" "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}"; then \
      echo "Installed CUDA-capable torch/torchvision build"; \
    else \
      echo "CUDA torch build unavailable, using CPU torch/torchvision build"; \
      pip install --no-cache-dir --index-url "${TORCH_CPU_INDEX_URL}" "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}"; \
    fi

COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt

# Install ONNX Runtime last so dependency resolution (e.g. insightface -> onnxruntime)
# cannot silently replace GPU runtime with CPU runtime. The 1.18.0 PyPI wheel
# links CUDA 11 libraries (libcublas.so.11, libcufft.so.10, libcurand.so.10),
# while torch itself still uses the separate cu121 wheel installed above.
ARG ONNXRUNTIME_GPU_SPEC=onnxruntime-gpu==1.18.0
ARG ONNXRUNTIME_CPU_SPEC=onnxruntime==1.18.0
ARG CUDA_RUNTIME_CU11_SPEC=nvidia-cuda-runtime-cu11==11.8.89
ARG CUDA_NVRTC_CU11_SPEC=nvidia-cuda-nvrtc-cu11==11.8.89
ARG CUBLAS_CU11_SPEC=nvidia-cublas-cu11==11.11.3.6
ARG CUDNN_CU11_SPEC=nvidia-cudnn-cu11==8.9.5.30
ARG CUFFT_CU11_SPEC=nvidia-cufft-cu11==10.9.0.58
ARG CURAND_CU11_SPEC=nvidia-curand-cu11==10.3.0.86
RUN set -eux; \
    pip uninstall -y onnxruntime onnxruntime-gpu || true; \
    if pip install --no-cache-dir -c constraints.txt "${ONNXRUNTIME_GPU_SPEC}"; then \
      echo "Installed onnxruntime-gpu"; \
      pip install --no-cache-dir -c constraints.txt \
        "${CUDA_RUNTIME_CU11_SPEC}" \
        "${CUDA_NVRTC_CU11_SPEC}" \
        "${CUBLAS_CU11_SPEC}" \
        "${CUDNN_CU11_SPEC}" \
        "${CUFFT_CU11_SPEC}" \
        "${CURAND_CU11_SPEC}"; \
    else \
      echo "onnxruntime-gpu unavailable, using onnxruntime (CPU)"; \
      pip install --no-cache-dir -c constraints.txt "${ONNXRUNTIME_CPU_SPEC}"; \
    fi

# Re-pin torch last to avoid resolver upgrades from transitive deps (e.g. transformers)
# that can select a newer CUDA build unsupported by older host drivers.
RUN set -eux; \
    if pip install --no-cache-dir --index-url "${TORCH_GPU_INDEX_URL}" "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}"; then \
      echo "Re-pinned CUDA torch/torchvision build"; \
    else \
      echo "CUDA torch re-pin unavailable, using CPU torch/torchvision build"; \
      pip install --no-cache-dir --index-url "${TORCH_CPU_INDEX_URL}" "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}"; \
    fi

RUN python -c "import torch, onnxruntime as ort; print('torch', torch.__version__, 'cuda', torch.version.cuda); print('onnxruntime', ort.__version__, ort.get_available_providers())"

COPY app.py .

EXPOSE 8000
CMD ["python", "app.py"]

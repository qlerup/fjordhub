# Download and cache ONNX face detection/recognition models for insightface
import insightface
import torch

try:
    import onnxruntime as ort
except Exception:
    ort = None


def _face_ctx_id() -> int:
    if not torch.cuda.is_available() or ort is None:
        return -1
    try:
        providers = [str(p) for p in ort.get_available_providers()]
    except Exception:
        providers = []
    return 0 if "CUDAExecutionProvider" in providers else -1

# Download face detection and recognition models (first run will cache them)
def download_models():
    print("Downloading face detection model...")
    detector = insightface.model_zoo.get_model('buffalo_l')
    detector.prepare(ctx_id=_face_ctx_id())
    print("Models downloaded and ready.")

if __name__ == "__main__":
    download_models()

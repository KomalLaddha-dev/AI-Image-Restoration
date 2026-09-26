import torch
import sys

def main():
    print(f"Python version: {sys.version}")
    print(f"Torch version: {torch.__version__}")
    if hasattr(torch.version, 'cuda'):
        print(f"CUDA version: {torch.version.cuda}")
    else:
        print("CUDA version: Not compiled with CUDA")
        
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i} name: {torch.cuda.get_device_name(i)}")
            print(f"GPU {i} memory: {props.total_memory / (1024**3):.2f} GB")
    else:
        print("No GPU detected by PyTorch.")

if __name__ == "__main__":
    main()

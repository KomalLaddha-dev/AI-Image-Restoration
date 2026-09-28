import os
import cv2
import asyncio
import glob
import subprocess
import json
import sys
from collections import defaultdict

def setup_directories():
    clean_dir = os.path.join("data", "eval", "clean")
    degraded_dir = os.path.join("data", "eval", "degraded")
    restored_dir = os.path.join("data", "eval", "restored")
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(degraded_dir, exist_ok=True)
    os.makedirs(restored_dir, exist_ok=True)
    return clean_dir, degraded_dir, restored_dir

def get_configs():
    return {
        "Config 1 (Original)": ["old_photo_repair", "colorize", "denoise", "face_restore", "upscale"],
        "Config 2 (Colorize First)": ["colorize", "old_photo_repair", "denoise", "face_restore", "upscale"],
        "Config 3 (Face Restore Early)": ["old_photo_repair", "face_restore", "colorize", "denoise", "upscale"],
        "Config 4 (Face Restore First)": ["face_restore", "old_photo_repair", "colorize", "denoise", "upscale"]
    }

async def run_single_config(config_name, stage_order_strs):
    from app.ml.pipeline import RestorationPipeline
    from app.models.schemas import RestoreOptions, RestorationStage, RestorationMode
    from app.eval.metrics import evaluate_image_quality, unload_lpips_model
    
    clean_dir = os.path.join("data", "eval", "clean")
    degraded_dir = os.path.join("data", "eval", "degraded")
    restored_dir = os.path.join("data", "eval", "restored")
    
    clean_images = glob.glob(os.path.join(clean_dir, "*.jpg")) + glob.glob(os.path.join(clean_dir, "*.png"))
    
    pipeline = RestorationPipeline()
    # Map string names back to enums
    pipeline.STAGE_ORDER = [RestorationStage(s) for s in stage_order_strs]
    
    options = RestoreOptions(
        denoise=True,
        face_restore=True,
        colorize=True,
        mode=RestorationMode.ADVANCED
    )
    
    config_restored_dir = os.path.join(restored_dir, config_name.replace(" ", "_").replace("(", "").replace(")", ""))
    os.makedirs(config_restored_dir, exist_ok=True)
    
    metrics_results = {'psnr': [], 'ssim': [], 'lpips': [], 'error': []}
    
    for clean_path in clean_images:
        basename = os.path.basename(clean_path)
        degraded_path = os.path.join(degraded_dir, basename)
        restored_path = os.path.join(config_restored_dir, basename)
        
        degraded_img = cv2.imread(degraded_path)
        try:
            result = await pipeline.restore(degraded_img, options)
            cv2.imwrite(restored_path, result.restored)
            metrics = evaluate_image_quality(clean_path, restored_path)
            metrics_results['psnr'].append(metrics['psnr'])
            metrics_results['ssim'].append(metrics['ssim'])
            metrics_results['lpips'].append(metrics['lpips'])
        except Exception as e:
            print(f"Error running {config_name} on {basename}: {e}")
            metrics_results['error'].append(str(e))
            
    # Print JSON result to stdout so the parent process can read it
    print("---RESULT_START---")
    print(json.dumps(metrics_results))
    print("---RESULT_END---")

def run_evaluation():
    clean_dir, degraded_dir, restored_dir = setup_directories()
    clean_images = glob.glob(os.path.join(clean_dir, "*.jpg")) + glob.glob(os.path.join(clean_dir, "*.png"))
    
    if not clean_images:
        print(f"No clean images found in {clean_dir}. Please add some ground truth images.")
        return
        
    print(f"Found {len(clean_images)} images. Synthesizing degradation...")
    from app.eval.degrade import synthesize_degradation
    for clean_path in clean_images:
        basename = os.path.basename(clean_path)
        degraded_path = os.path.join(degraded_dir, basename)
        if not os.path.exists(degraded_path):
            synthesize_degradation(clean_path, degraded_path)
            
    configs = get_configs()
    results = {}
    
    for config_name, stage_order_strs in configs.items():
        print(f"\nRunning {config_name} in isolated subprocess...")
        env = os.environ.copy()
        env["EVAL_RUN_CONFIG"] = config_name
        env["EVAL_STAGE_ORDER"] = json.dumps(stage_order_strs)
        
        process = subprocess.run(
            [sys.executable, "-m", "app.eval.run_eval"],
            env=env,
            capture_output=True,
            text=True
        )
        
        print(process.stderr)
        
        # Parse result from stdout
        metrics_results = None
        output = process.stdout
        if "---RESULT_START---" in output and "---RESULT_END---" in output:
            try:
                json_str = output.split("---RESULT_START---")[1].split("---RESULT_END---")[0].strip()
                metrics_results = json.loads(json_str)
            except Exception as e:
                print(f"Failed to parse subprocess output: {e}")
                
        if metrics_results:
            results[config_name] = metrics_results
        else:
            print(f"Subprocess failed for {config_name}. Check logs.")
            print("STDOUT:", output)
            results[config_name] = {'error': ['Subprocess crashed (OOM?)']}
            
    report_path = os.path.join("data", "eval", "results.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Synthetic Degradation Evaluation Results\n\n")
        f.write("| Configuration | PSNR (↑) | SSIM (↑) | LPIPS (↓) |\n")
        f.write("|--------------|----------|----------|-----------|\n")
        
        for config_name in configs:
            config_res = results.get(config_name, {})
            if config_res.get('error'):
                f.write(f"| {config_name} | FAILED (OOM) | FAILED | FAILED |\n")
            elif len(config_res.get('psnr', [])) > 0:
                avg_psnr = sum(config_res['psnr']) / len(config_res['psnr'])
                avg_ssim = sum(config_res['ssim']) / len(config_res['ssim'])
                avg_lpips = sum(config_res['lpips']) / len(config_res['lpips'])
                f.write(f"| {config_name} | {avg_psnr:.2f} | {avg_ssim:.4f} | {avg_lpips:.4f} |\n")
            else:
                f.write(f"| {config_name} | N/A | N/A | N/A |\n")
                
    print(f"\nEvaluation complete. Results written to {report_path}")

if __name__ == "__main__":
    if "EVAL_RUN_CONFIG" in os.environ:
        config_name = os.environ["EVAL_RUN_CONFIG"]
        stage_order_strs = json.loads(os.environ["EVAL_STAGE_ORDER"])
        asyncio.run(run_single_config(config_name, stage_order_strs))
    else:
        run_evaluation()

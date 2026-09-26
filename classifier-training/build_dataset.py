import os
import time
from pathlib import Path
from bing_image_downloader import downloader
from loguru import logger

# List of 50 prominent Indian monuments
MONUMENTS = [
    "taj_mahal", "qutub_minar", "red_fort", "hawa_mahal", "charminar",
    "gateway_of_india", "india_gate", "sanchi_stupa", "ajanta_caves", "ellora_caves",
    "mysore_palace", "victoria_memorial", "golden_temple", "sun_temple_konark", "meenakshi_temple",
    "brihadisvara_temple", "hampi_chariot", "khajuraho_temples", "fatehpur_sikri", "agra_fort",
    "amber_fort", "mehrangarh_fort", "gwalior_fort", "golconda_fort", "jantar_mantar_jaipur",
    "lotus_temple", "akshardham_temple_delhi", "kashi_vishwanath_temple", "somnath_temple", "jagannath_temple_puri",
    "elephanta_caves", "badami_cave_temples", "pattadakal_monuments", "mahabalipuram_shore_temple", "chhatrapati_shivaji_terminus",
    "gol_gumbaz", "bara_imambara", "city_palace_udaipur", "lake_palace_udaipur", "jal_mahal",
    "chitradurga_fort", "kumbalgarh_fort", "rani_ki_vav", "champaner_pavagadh", "bhimbetka_rock_shelters",
    "nalanda_university_ruins", "mahabodhi_temple", "safdarjung_tomb", "humayun_tomb", "purana_qila"
]

def download_images(monument: str, num_images: int = 50, output_dir: str = "dataset"):
    """Downloads images for a specific monument using Bing search."""
    search_term = monument.replace("_", " ") + " monument india"
    
    logger.info(f"Downloading {num_images} images for {search_term}...")
    
    try:
        downloader.download(
            search_term, 
            limit=num_images, 
            output_dir=output_dir, 
            adult_filter_off=True, 
            force_replace=False, 
            timeout=10, 
            verbose=False
        )
    except Exception as e:
        logger.error(f"Error searching for {monument}: {e}")
        return

def split_train_val(output_dir: str = "dataset"):
    """Moves 20% of downloaded images to the val/ directory."""
    import shutil
    
    base_dir = Path(output_dir)
    train_dir = base_dir / "train"
    val_dir = base_dir / "val"
    train_dir.mkdir(exist_ok=True)
    val_dir.mkdir(exist_ok=True)
    
    # bing-image-downloader puts images in output_dir/search_term
    for monument in MONUMENTS:
        search_term = monument.replace("_", " ") + " monument india"
        source_dir = base_dir / search_term
        
        if not source_dir.exists():
            continue
            
        monument_train = train_dir / monument
        monument_val = val_dir / monument
        monument_train.mkdir(exist_ok=True)
        monument_val.mkdir(exist_ok=True)
        
        images = list(source_dir.glob("*.*"))
        for idx, img_path in enumerate(images):
            # 80/20 split
            is_val = idx % 5 == 0
            target_dir = monument_val if is_val else monument_train
            shutil.move(str(img_path), str(target_dir / img_path.name))
            
        # Remove original dir if empty
        try:
            source_dir.rmdir()
        except:
            pass

def main():
    dataset_dir = Path("dataset")
    dataset_dir.mkdir(exist_ok=True)
    
    for monument in MONUMENTS:
        logger.info(f"--- Processing {monument} ---")
        download_images(monument, num_images=60, output_dir=str(dataset_dir))
        
    logger.info("Splitting dataset into train/val...")
    split_train_val(str(dataset_dir))

if __name__ == "__main__":
    main()

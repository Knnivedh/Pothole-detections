"""
🎯 POTHOLE DETECTION USING CUSTOM PRE-TRAINED MODEL
Simple and efficient pothole detection using your best.pt model
"""

import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from tqdm import tqdm
import logging
from dataclasses import dataclass
from typing import List, Optional

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("❌ Please install ultralytics: pip install ultralytics")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PotholeDetection:
    """Pothole detection data structure"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    def to_yolo_format(self, img_width: int, img_height: int) -> str:
        """Convert to YOLO format (class x_center y_center width height)"""
        x_center = (self.x + self.width/2) / img_width
        y_center = (self.y + self.height/2) / img_height
        norm_width = self.width / img_width
        norm_height = self.height / img_height
        return f"0 {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}"

class PotholeDetector:
    """Simple pothole detector using your custom model"""
    
    def __init__(self, model_path: str = "best.pt"):
        self.model_path = Path(model_path)
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load your custom pre-trained model"""
        if not self.model_path.exists():
            logger.error(f"❌ Model not found: {self.model_path}")
            return
        
        try:
            logger.info(f"🔥 Loading custom model: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            logger.info(f"✅ Model loaded! Classes: {self.model.names}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
    
    def detect(self, image: np.ndarray, conf_threshold: float = 0.25) -> List[PotholeDetection]:
        """Detect potholes in image"""
        if self.model is None:
            return []
        
        detections = []
        try:
            results = self.model(image, conf=conf_threshold, verbose=False)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        
                        detection = PotholeDetection(
                            x=int(x1), y=int(y1), 
                            width=int(x2-x1), height=int(y2-y1),
                            confidence=conf
                        )
                        detections.append(detection)
        except Exception as e:
            logger.error(f"Detection failed: {e}")
        
        return detections
    
    def visualize(self, image: np.ndarray, detections: List[PotholeDetection]) -> np.ndarray:
        """Create visualization"""
        vis_image = image.copy()
        
        for i, det in enumerate(detections):
            # Color based on confidence
            if det.confidence > 0.7:
                color = (0, 255, 0)  # Green
            elif det.confidence > 0.5:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 0, 255)  # Red
            
            # Draw box
            cv2.rectangle(vis_image, (det.x, det.y), 
                         (det.x + det.width, det.y + det.height), color, 2)
            
            # Add label
            label = f"Pothole {det.confidence:.2f}"
            cv2.putText(vis_image, label, (det.x, det.y-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return vis_image

def process_images(input_dir: str, output_dir: str = "results"):
    """Process all images in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directories
    (output_path / "labels").mkdir(parents=True, exist_ok=True)
    (output_path / "visualizations").mkdir(parents=True, exist_ok=True)
    
    # Initialize detector
    detector = PotholeDetector()
    if detector.model is None:
        return
    
    # Get image files
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))
    
    total_detections = 0
    processed_count = 0
    
    logger.info(f"🚀 Processing {len(image_files)} images...")
    
    for image_file in tqdm(image_files, desc="🎯 Detecting Potholes"):
        try:
            # Load image
            image = cv2.imread(str(image_file))
            if image is None:
                continue
            
            # Detect potholes
            detections = detector.detect(image)
            total_detections += len(detections)
            processed_count += 1
            
            # Save YOLO labels
            if detections:
                label_file = output_path / "labels" / f"{image_file.stem}.txt"
                with open(label_file, 'w') as f:
                    for det in detections:
                        f.write(det.to_yolo_format(image.shape[1], image.shape[0]) + "\\n")
            
            # Save visualization (first 50 only)
            if processed_count <= 50:
                vis_image = detector.visualize(image, detections)
                vis_file = output_path / "visualizations" / f"vis_{image_file.name}"
                cv2.imwrite(str(vis_file), vis_image)
        
        except Exception as e:
            logger.error(f"Error processing {image_file.name}: {e}")
    
    # Save summary
    summary = {
        "images_processed": processed_count,
        "total_detections": total_detections,
        "average_per_image": total_detections / max(processed_count, 1),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(output_path / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print results
    print(f"\\n🎯 RESULTS:")
    print(f"📸 Images: {processed_count}")
    print(f"🕳️ Potholes: {total_detections}")
    print(f"📊 Average: {summary['average_per_image']:.1f} per image")
    print(f"📁 Output: {output_path}")

if __name__ == "__main__":
    # Configuration
    IMAGES_DIR = r"C:\\Users\\Gourav Bhat\\Downloads\\archive\\potholes"
    OUTPUT_DIR = "pothole_results"
    
    print("🎯 POTHOLE DETECTION WITH CUSTOM MODEL")
    print("=" * 50)
    
    process_images(IMAGES_DIR, OUTPUT_DIR)
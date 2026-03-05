import os
import json
import subprocess
from pathlib import Path

# Mock JSON data adhering strictly to tools/MASTER_PROMPT.md
mock_data = {
  "asin": "B0TEST1234",
  "title": "Mock Product - High Capacity Portable Charger 10000mAh",
  "bullets": [
    "High capacity 10000mAh portable charger.",
    "Fast charging support with USB-C.",
    "Compact and lightweight design."
  ],
  "clr": {
    "brand": "MockBrand",
    "manufacturer": "MockMfg",
    "item_name": "Mock Product - High Capacity Portable Charger 10000mAh",
    "battery_capacity": "10000",
    "item_weight": "200"
  },
  "spec": {
    "capacity_mah": 10000,
    "usb_c_output": "18W"
  },
  "btg": {
    "category": "Cell Phones & Accessories",
    "node_id": "2407749011",
    "node_path": "Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks"
  },
  "keywords": [
    "portable charger",
    "power bank 10000mah",
    "fast charging power bank"
  ],
  "topic_clusters": {
    "charging_speed": [
      "How fast does it charge a phone?",
      "Does it support 18W fast charging?"
    ],
    "compatibility": [
      "Does it work with recent phones?"
    ]
  },
  "reviews": [
    {
      "text": "Great portable charger, very fast and reliable.",
      "rating": 5
    }
  ],
  "competitor_qas": [
    {
      "question": "Can I carry this on an airplane?",
      "answer": "Yes, it is TSA approved."
    }
  ],
  "product_context": {
    "waterproof_rating": "None",
    "warranty_months": 12,
    "charge_hours": 3
  },
  "images": [
    {
      "filename": "main.jpg",
      "image_type": "main",
      "alt_text": "Mock Product Main Image",
      "ocr_text": ""
    }
  ],
  "comparison_table": {
    "Battery Capacity": {"This ASIN": "10000mAh", "Competitor 1": "5000mAh"}
  },
  "modules": [
    {
      "type": "technical_specs",
      "content": "Capacity: 10000mAh, Output: 18W USB-C."
    }
  ],
  "product_claims": [
    "Charges to 50% in 30 mins"
  ],
  "videos": [],
  "category_path": "Cell Phones & Accessories > Accessories > Chargers & Power Adapters > Portable Power Banks",
  "market": "us"
}

def main():
    print("Starting Automation Pipeline...")
    input_dir = Path("input_jsons")
    input_dir.mkdir(exist_ok=True)
    
    file_path = input_dir / "test_product.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)
    print(f"Generated input JSON at {file_path}")
    
    run_batch_script = Path("run_batch.py")
    if not run_batch_script.exists():
        print("Error: run_batch.py not found.")
        return
        
    cmd = ["python", str(run_batch_script), "--input-dir", str(input_dir), "--report"]
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("Automation loop successfully piped data and completed.")
    else:
        print("Automation loop failed.")

if __name__ == "__main__":
    main()

import argparse
import sys
from pathlib import Path
import subprocess

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description="Run the Rufus pipeline in batch mode.")
    parser.add_argument("--input-dir", required=True, help="Directory containing input JSON files")
    parser.add_argument("--report", action="store_true", help="Generate HTML report via Skill 08")
    parser.add_argument("--infographics", action="store_true", help="Generate InfoGraphics via Skill 09")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory {input_dir} is not valid.")
        sys.exit(1)

    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}.")
        sys.exit(0)

    print(f"Found {len(json_files)} files to process in batch mode.")
    
    success_count = 0
    failure_count = 0

    run_product_script = _HERE / "run_product.py"

    for i, json_file in enumerate(json_files, 1):
        print("\n" + "="*70)
        print(f"  PROCESSING ITEM {i}/{len(json_files)}: {json_file.name}")
        print("="*70)

        cmd = [sys.executable, str(run_product_script), "--input", str(json_file)]
        if args.report:
            cmd.append("--report")
        if args.infographics:
            cmd.append("--infographics")

        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                success_count += 1
            else:
                failure_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Error processing {json_file.name}: {e}")
            failure_count += 1
        except Exception as e:
            print(f"Unexpected error on {json_file.name}: {e}")
            failure_count += 1

    print("\n" + "="*70)
    print(f"  BATCH PROCESSING COMPLETE")
    print(f"  Success: {success_count} | Failed: {failure_count} | Total: {len(json_files)}")
    print("="*70)

if __name__ == "__main__":
    main()

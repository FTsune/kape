from pathlib import Path
import sys

# Get the absolute path of the current file
FILE = Path(__file__).resolve()
# Get the parent directory of the current file
ROOT = FILE.parent
# Add the root path to the sys.path list if it is not already there
if ROOT not in sys.path:
    sys.path.append(str(ROOT))
# Get the relative path of the root directory with respect to the current working directory
ROOT = ROOT.relative_to(Path.cwd())

# Sources
IMAGE = "Image"

SOURCES_LIST = [IMAGE]

# Images config
IMAGES_DIR = ROOT / "../../static/images"
DEFAULT_IMAGE = IMAGES_DIR / "DB2.jpg"
DEFAULT_DETECT_IMAGE = IMAGES_DIR / "DB.jpg"


# ML Model config
MODEL_DIR = ROOT / "../../weights"

DISEASE_MODEL_SPOTS = MODEL_DIR / "spots.pt" 
DISEASE_LIGHTWEIGHT_MODEL = MODEL_DIR / "yolo12n.pt"
DISEASE_MODEL_YOLO12M = MODEL_DIR / "yolo11m96.pt" 

LEAF_MODEL = MODEL_DIR / "cleaf.pt"  # unchanged

import shutil
import os

brain_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\b965e400-f776-435f-bd61-c41cdb30fc25"
dest_dir = r"c:\Users\LENOVO\OneDrive\Pictures\Desktop\KT1(game)"

# Xóa các ảnh cũ để tránh xung đột
old_files = ["weapon_ui.png", "weapon_ui_backup.png"]
for f in old_files:
    path = os.path.join(dest_dir, f)
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted old file: {f}")

mapping = {
    "media__1779207651718.png": "pistol.png",
    "media__1779207657799.png": "shotgun.png",
    "media__1779207911074.png": "smg.png",
    "media__1779207920132.png": "sniper.png",
    "media__1779207924813.png": "advanced_sniper.png",
    "media__1779206471466.png": "weapon_ui.png",
    "media__1779206471466.png": "weapon_ui_backup.png"
}

for src_name, dest_name in mapping.items():
    src_path = os.path.join(brain_dir, src_name)
    dest_path = os.path.join(dest_dir, dest_name)
    if os.path.exists(src_path):
        shutil.copy(src_path, dest_path)
        print(f"Copied {src_name} to {dest_name} successfully!")
    else:
        print(f"Source file {src_name} not found!")

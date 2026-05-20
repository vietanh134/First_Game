from PIL import Image

def main():
    img = Image.open('weapon_ui_backup.png')
    print(f"Dimensions: {img.size}")
    print(f"Format: {img.format}")

if __name__ == '__main__':
    main()

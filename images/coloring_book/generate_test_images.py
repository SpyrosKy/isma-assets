import numpy as np
from PIL import Image, ImageDraw
import os

# Créer le répertoire de sortie s'il n'existe pas
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

def create_flower():
    # Créer une image de contour (outline)
    outline_img = Image.new('RGBA', (400, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(outline_img)
    
    # Dessiner le contour de la fleur
    # Centre
    draw.ellipse((175, 175, 225, 225), outline='black', width=2)
    
    # Pétales
    for i in range(8):
        angle = i * 45
        x = 200 + 100 * np.cos(np.radians(angle))
        y = 200 + 100 * np.sin(np.radians(angle))
        draw.ellipse((x-40, y-40, x+40, y+40), outline='black', width=2)
    
    # Tige
    draw.line((200, 225, 200, 350), fill='black', width=2)
    
    # Feuilles
    draw.arc((150, 280, 200, 330), 0, 180, fill='black', width=2)
    draw.arc((200, 280, 250, 330), 0, 180, fill='black', width=2)
    
    # Créer une image de masque
    mask_img = Image.new('RGB', (400, 400), (255, 255, 255))
    mask_draw = ImageDraw.Draw(mask_img)
    
    # Centre (région 1)
    mask_draw.ellipse((175, 175, 225, 225), fill=(1, 0, 0))
    
    # Pétales (région 2)
    for i in range(8):
        angle = i * 45
        x = 200 + 100 * np.cos(np.radians(angle))
        y = 200 + 100 * np.sin(np.radians(angle))
        mask_draw.ellipse((x-40, y-40, x+40, y+40), fill=(2, 0, 0))
    
    # Tige (région 3)
    points = [(198, 225), (202, 225), (202, 350), (198, 350)]
    mask_draw.polygon(points, fill=(3, 0, 0))
    
    # Feuilles (région 4)
    for i in range(150, 200):
        for j in range(280, 330):
            if (i-150)**2 + (j-305)**2 <= 25**2 and j < 305:
                mask_img.putpixel((i, j), (4, 0, 0))
    
    for i in range(200, 250):
        for j in range(280, 330):
            if (i-250)**2 + (j-305)**2 <= 25**2 and j < 305:
                mask_img.putpixel((i, j), (4, 0, 0))
    
    # Sauvegarder les images
    outline_img.save(os.path.join(output_dir, "outline_flower.png"))
    mask_img.save(os.path.join(output_dir, "mask_flower.png"))
    
    # Créer le fichier palette JSON
    palette_json = """
    [
        {"number": 1, "color": "#FFEB3B"},
        {"number": 2, "color": "#FF9800"},
        {"number": 3, "color": "#4CAF50"},
        {"number": 4, "color": "#8BC34A"}
    ]
    """
    with open(os.path.join(output_dir, "palette_flower.json"), "w") as f:
        f.write(palette_json.strip())

def create_butterfly():
    # Créer une image de contour (outline)
    outline_img = Image.new('RGBA', (400, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(outline_img)
    
    # Dessiner le contour du papillon
    # Corps
    draw.line((200, 150, 200, 250), fill='black', width=2)
    
    # Antennes
    draw.line((200, 150, 180, 120), fill='black', width=2)
    draw.line((200, 150, 220, 120), fill='black', width=2)
    
    # Ailes
    # Aile supérieure gauche
    points1 = [(200, 170), (120, 120), (100, 180), (160, 200)]
    draw.polygon(points1, outline='black')
    
    # Aile supérieure droite
    points2 = [(200, 170), (280, 120), (300, 180), (240, 200)]
    draw.polygon(points2, outline='black')
    
    # Aile inférieure gauche
    points3 = [(200, 200), (140, 200), (100, 260), (180, 240)]
    draw.polygon(points3, outline='black')
    
    # Aile inférieure droite
    points4 = [(200, 200), (260, 200), (300, 260), (220, 240)]
    draw.polygon(points4, outline='black')
    
    # Créer une image de masque
    mask_img = Image.new('RGB', (400, 400), (255, 255, 255))
    mask_draw = ImageDraw.Draw(mask_img)
    
    # Corps (région 1)
    points_body = [(198, 150), (202, 150), (202, 250), (198, 250)]
    mask_draw.polygon(points_body, fill=(1, 0, 0))
    
    # Antennes (région 1 aussi)
    points_ant1 = [(199, 150), (201, 150), (181, 120), (179, 120)]
    mask_draw.polygon(points_ant1, fill=(1, 0, 0))
    
    points_ant2 = [(199, 150), (201, 150), (221, 120), (219, 120)]
    mask_draw.polygon(points_ant2, fill=(1, 0, 0))
    
    # Ailes
    # Aile supérieure gauche (région 2)
    mask_draw.polygon(points1, fill=(2, 0, 0))
    
    # Aile supérieure droite (région 3)
    mask_draw.polygon(points2, fill=(3, 0, 0))
    
    # Aile inférieure gauche (région 4)
    mask_draw.polygon(points3, fill=(4, 0, 0))
    
    # Aile inférieure droite (région 5)
    mask_draw.polygon(points4, fill=(5, 0, 0))
    
    # Sauvegarder les images
    outline_img.save(os.path.join(output_dir, "outline_butterfly.png"))
    mask_img.save(os.path.join(output_dir, "mask_butterfly.png"))
    
    # Créer le fichier palette JSON
    palette_json = """
    [
        {"number": 1, "color": "#000000"},
        {"number": 2, "color": "#E91E63"},
        {"number": 3, "color": "#9C27B0"},
        {"number": 4, "color": "#2196F3"},
        {"number": 5, "color": "#03A9F4"}
    ]
    """
    with open(os.path.join(output_dir, "palette_butterfly.json"), "w") as f:
        f.write(palette_json.strip())

def create_cat():
    # Créer une image de contour (outline)
    outline_img = Image.new('RGBA', (400, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(outline_img)
    
    # Dessiner le contour du chat
    # Tête
    draw.ellipse((150, 150, 250, 250), outline='black', width=2)
    
    # Oreilles
    draw.polygon([(160, 160), (140, 120), (180, 140)], outline='black')
    draw.polygon([(240, 160), (260, 120), (220, 140)], outline='black')
    
    # Yeux
    draw.ellipse((170, 180, 190, 200), outline='black', width=2)
    draw.ellipse((210, 180, 230, 200), outline='black', width=2)
    
    # Pupilles
    draw.ellipse((175, 185, 185, 195), fill='black')
    draw.ellipse((215, 185, 225, 195), fill='black')
    
    # Nez
    draw.polygon([(200, 200), (190, 210), (210, 210)], outline='black')
    
    # Bouche
    draw.arc((180, 210, 220, 230), 0, 180, fill='black', width=2)
    
    # Moustaches
    draw.line((190, 210, 150, 200), fill='black')
    draw.line((190, 215, 150, 215), fill='black')
    draw.line((210, 210, 250, 200), fill='black')
    draw.line((210, 215, 250, 215), fill='black')
    
    # Créer une image de masque
    mask_img = Image.new('RGB', (400, 400), (255, 255, 255))
    mask_draw = ImageDraw.Draw(mask_img)
    
    # Tête (région 1)
    mask_draw.ellipse((150, 150, 250, 250), fill=(1, 0, 0))
    
    # Oreilles (région 2)
    mask_draw.polygon([(160, 160), (140, 120), (180, 140)], fill=(2, 0, 0))
    mask_draw.polygon([(240, 160), (260, 120), (220, 140)], fill=(2, 0, 0))
    
    # Yeux blancs (région 3)
    mask_draw.ellipse((170, 180, 190, 200), fill=(3, 0, 0))
    mask_draw.ellipse((210, 180, 230, 200), fill=(3, 0, 0))
    
    # Pupilles (région 4)
    mask_draw.ellipse((175, 185, 185, 195), fill=(4, 0, 0))
    mask_draw.ellipse((215, 185, 225, 195), fill=(4, 0, 0))
    
    # Nez (région 5)
    mask_draw.polygon([(200, 200), (190, 210), (210, 210)], fill=(5, 0, 0))
    
    # Sauvegarder les images
    outline_img.save(os.path.join(output_dir, "outline_cat.png"))
    mask_img.save(os.path.join(output_dir, "mask_cat.png"))
    
    # Créer le fichier palette JSON
    palette_json = """
    [
        {"number": 1, "color": "#FFA726"},
        {"number": 2, "color": "#FF7043"},
        {"number": 3, "color": "#FFFFFF"},
        {"number": 4, "color": "#000000"},
        {"number": 5, "color": "#FF80AB"}
    ]
    """
    with open(os.path.join(output_dir, "palette_cat.json"), "w") as f:
        f.write(palette_json.strip())

if __name__ == "__main__":
    create_flower()
    create_butterfly()
    create_cat()
    print("Images de test générées avec succès dans le dossier 'output'")

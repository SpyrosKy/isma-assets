import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import imutils
import os
import re
import shutil # Added for file operations

# --- CONFIGURATION ---
# MODIFICATION : Le script cherche maintenant les images dans le même dossier que lui.
IMAGES_DIRECTORY = "."
# Dossier pour les images avec un nombre incorrect de différences
INVALID_IMAGES_FOLDER = os.path.join(IMAGES_DIRECTORY, ".venv", "Images_with_less")
# Fichier de sortie pour le code Dart
DART_OUTPUT_FILE = "../../../lib/games/find_the_differences/components/level_data.dart"
# Préfixe du chemin d'accès utilisé dans votre application Flutter
ASSETS_PATH_PREFIX = "assets/images/find_the_differences/"
# Nombre de différences à trouver par image
NUM_DIFFERENCES_TARGET = 7
# Aire minimale pour qu'un contour soit considéré comme une différence (ignore le bruit)
MIN_CONTOUR_AREA = 20
# Rayon par défaut si une différence est trop petite (en pourcentage de la largeur)
DEFAULT_RADIUS_RATIO = 0.045


def process_image_pair(original_path, modified_path):
    """
    Analyse une paire d'images avec une méthode robuste aux artefacts JPEG.
    """
    image_originale = cv2.imread(original_path)
    image_modifiee = cv2.imread(modified_path)

    if image_originale is None or image_modifiee is None:
        print(f"  -> Erreur: Impossible de charger {original_path} ou {modified_path}")
        return []

    hauteur, largeur, _ = image_originale.shape
    image_modifiee = cv2.resize(image_modifiee, (largeur, hauteur))

    # --- Debugging level9 ---
    is_level9 = "level9" in original_path.lower()
    debug_dir = None
    if is_level9:
        debug_dir = os.path.join(os.path.dirname(original_path), "debug_level9")
        os.makedirs(debug_dir, exist_ok=True)
        print(f"  ---> DEBUGGING level9: Saving intermediate images to {debug_dir}")
    # --- End Debugging level9 ---

    gris_original = cv2.cvtColor(image_originale, cv2.COLOR_BGR2GRAY)
    gris_modifie = cv2.cvtColor(image_modifiee, cv2.COLOR_BGR2GRAY)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_1_gris_original.png"), gris_original)
        cv2.imwrite(os.path.join(debug_dir, "level9_1_gris_modifie.png"), gris_modifie)

    # --- DÉBUT DES MODIFICATIONS STRATÉGIQUES ---

    # NOUVELLE ETAPE 1: Flouter les deux images pour supprimer le bruit de compression JPEG
    # Le noyau (5, 5) est une bonne valeur de départ.
    blur_original = cv2.GaussianBlur(gris_original, (3, 3), 0)
    blur_modifie = cv2.GaussianBlur(gris_modifie, (3, 3), 0)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_2_blur_original.png"), blur_original)
        cv2.imwrite(os.path.join(debug_dir, "level9_2_blur_modifie.png"), blur_modifie)

    # METHODE DE COMPARAISON MODIFIÉE: Différence absolue sur les images floutées
    diff = cv2.absdiff(blur_original, blur_modifie)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_3_diff_abs.png"), diff)

    # SEUIL MODIFIÉ: On utilise un seuil fixe pour mieux contrôler la sensibilité
    # Une valeur entre 25 et 50 est généralement un bon point de départ.
    # Si des différences sont manquées, baissez cette valeur. Si trop de bruit est détecté, augmentez-la.
    _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_4_thresh.png"), thresh)
    
    # On garde les opérations morphologiques pour nettoyer et grouper le résultat
    # On réduit la taille du noyau de fermeture pour être moins agressif
    kernel_close = np.ones((3, 3), np.uint8)
    thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_5_thresh_closed.png"), thresh_closed)

    # On réduit la taille du noyau de dilatation pour éviter de fusionner les différences proches
    kernel_dilate = np.ones((7, 7), np.uint8)
    # On réduit le nombre d'itérations de dilatation
    thresh_dilated = cv2.dilate(thresh_closed, kernel_dilate, iterations=1)
    if is_level9 and debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "level9_6_thresh_dilated.png"), thresh_dilated)

    # --- FIN DES MODIFICATIONS STRATÉGIQUES ---

    contours = cv2.findContours(thresh_dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    filtered_contours = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]
    sorted_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True)
    
    # Vérifier si le nombre de contours trouvés est inférieur à la cible
    if len(sorted_contours) < NUM_DIFFERENCES_TARGET:
        print(f"  -> Avertissement: Trouvé seulement {len(sorted_contours)}/{NUM_DIFFERENCES_TARGET} différences significatives pour {os.path.basename(original_path)}. Ces images ne seront pas incluses et seront déplacées.")
        return None # Indique que le nombre de différences est incorrect

    # Si on arrive ici, on a au moins NUM_DIFFERENCES_TARGET contours. On prend les N meilleurs.
    top_contours = sorted_contours[:NUM_DIFFERENCES_TARGET]

    difference_spots = []
    # --- Debugging level9: Draw detected contours ---
    if is_level9 and debug_dir:
        img_with_contours = image_originale.copy()
        cv2.drawContours(img_with_contours, top_contours, -1, (0, 255, 0), 3) # Draw in green
        for spot_contour in top_contours: # Draw bounding boxes too
            (s_px, s_py, s_pw, s_ph) = cv2.boundingRect(spot_contour)
            cv2.rectangle(img_with_contours, (s_px, s_py), (s_px + s_pw, s_py + s_ph), (255, 0, 0), 2) # Blue rectangles
        cv2.imwrite(os.path.join(debug_dir, "level9_7_contours_detected.png"), img_with_contours)
    # --- End Debugging level9 ---

    for contour in top_contours:
        (px, py, pw, ph) = cv2.boundingRect(contour)
        center_x_px = px + pw / 2
        center_y_px = py + ph / 2
        norm_x = round(center_x_px / largeur, 4)
        norm_y = round(center_y_px / hauteur, 4)
        norm_radius = DEFAULT_RADIUS_RATIO
        difference_spots.append({'x': norm_x, 'y': norm_y, 'radius': norm_radius})

    # À ce point, len(difference_spots) sera NUM_DIFFERENCES_TARGET
    print(f"  -> Trouvé et retenu {len(difference_spots)}/{NUM_DIFFERENCES_TARGET} différences pour {os.path.basename(original_path)} (méthode robuste).")
    return difference_spots


def generate_dart_code():
    """
    Fonction principale qui scanne les images et génère le fichier Dart.
    """
    print("Démarrage du traitement des images...")
    
    # Le script va lister tous les fichiers, y compris lui-même, mais les filtres ne garderont que les images.
    all_files = sorted(os.listdir(IMAGES_DIRECTORY))
    image_pairs = []

    for filename in all_files:
        if "_original" in filename:
            modified_filename = filename.replace("_original", "_modified")
            if modified_filename in all_files:
                image_pairs.append({
                    "original": filename,
                    "modified": modified_filename
                })

    if not image_pairs:
        print(f"Erreur: Aucun couple d'images `_original` et `_modified` trouvé dans ce dossier.")
        return

    print(f"Trouvé {len(image_pairs)} paires d'images.")
    
    # Créer le dossier pour les images avec un nombre incorrect de différences s'il n'existe pas
    os.makedirs(INVALID_IMAGES_FOLDER, exist_ok=True)
    print(f"Les images avec moins de {NUM_DIFFERENCES_TARGET} différences seront déplacées vers: {INVALID_IMAGES_FOLDER}")
    
    all_levels_data_strings = []
    level_id_counter = 1 # Ce compteur ne s'incrémentera que pour les niveaux valides

    for pair in image_pairs:
        base_name = pair['original'].split("_original")[0]
        print(f"\nTraitement de la paire d'images pour '{base_name}'...") 
        
        original_full_path = os.path.join(IMAGES_DIRECTORY, pair['original'])
        modified_full_path = os.path.join(IMAGES_DIRECTORY, pair['modified'])
        
        spots = process_image_pair(original_full_path, modified_full_path)

        if spots is None: # Cas où le nombre de différences n'est pas NUM_DIFFERENCES_TARGET
            print(f"  -> Déplacement des images pour {base_name} car le nombre de différences détectées n'est pas {NUM_DIFFERENCES_TARGET}.")
            
            dest_original_path = os.path.join(INVALID_IMAGES_FOLDER, pair['original'])
            dest_modified_path = os.path.join(INVALID_IMAGES_FOLDER, pair['modified'])
            
            try:
                if os.path.exists(original_full_path):
                    shutil.move(original_full_path, dest_original_path)
                
                if os.path.exists(modified_full_path):
                    shutil.move(modified_full_path, dest_modified_path)

                moved_original = os.path.exists(dest_original_path) and not os.path.exists(original_full_path)
                moved_modified = os.path.exists(dest_modified_path) and not os.path.exists(modified_full_path)

                if moved_original or moved_modified :
                     print(f"     Images pour {base_name} déplacées vers {INVALID_IMAGES_FOLDER}")
                elif (os.path.exists(dest_original_path) or os.path.exists(dest_modified_path)) and \
                     not (os.path.exists(original_full_path) or os.path.exists(modified_full_path)):
                     print(f"     Images pour {base_name} semblent déjà déplacées ou sources supprimées.")
                # else: # Commented out for brevity, can be enabled for detailed debugging
                #      print(f"     Vérification du déplacement pour {base_name}: src_orig_exists={os.path.exists(original_full_path)}, src_mod_exists={os.path.exists(modified_full_path)}, dest_orig_exists={os.path.exists(dest_original_path)}, dest_mod_exists={os.path.exists(dest_modified_path)}")

            except Exception as e:
                print(f"     Erreur critique lors du déplacement des images {base_name}: {e}")
            continue 

        if not spots: # Cas où process_image_pair retourne une liste vide (ex: erreur de chargement d'image)
            print(f"  -> Aucune différence traitable trouvée pour {base_name} (ex: erreur chargement), couple ignoré.")
            continue
        
        # Si on arrive ici, le niveau est valide. On peut maintenant utiliser level_id_counter.
        print(f"  -> Niveau {level_id_counter} ({base_name}) validé avec {len(spots)} différences.")

        diff_spots_strings = []
        for i, spot in enumerate(spots):
            spot_string = f"      DifferenceSpot(id: 'diff{i+1}', x: {spot['x']}, y: {spot['y']}, radius: {spot['radius']})"
            diff_spots_strings.append(spot_string)

        level_data_string = f"""  LevelData(
    levelId: '{level_id_counter}',
    imageOriginalPath: '{ASSETS_PATH_PREFIX}{pair['original']}',
    imageModifiedPath: '{ASSETS_PATH_PREFIX}{pair['modified']}',
    differences: [
{',\n'.join(diff_spots_strings)},
    ],
    totalDifferences: {len(spots)},
  )"""
        
        all_levels_data_strings.append(level_data_string)
        level_id_counter += 1

    level_data_class_definition = """\nimport 'difference_spot.dart';

class LevelData {
  final String levelId;
  final String imageOriginalPath;
  final String imageModifiedPath;
  final List<DifferenceSpot> differences;
  final int timeLimitSeconds; // Default can be set here or in constructor
  final int totalDifferences;

  LevelData({
    required this.levelId,
    required this.imageOriginalPath,
    required this.imageModifiedPath,
    required this.differences,
    this.timeLimitSeconds = 120, // Example default value
    required this.totalDifferences,
  });
}
"""

    final_dart_content = f"// Fichier auto-généré le {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    final_dart_content += level_data_class_definition
    final_dart_content += "\nfinal List<LevelData> levels = [\n"
    if all_levels_data_strings:
        final_dart_content += ",\n".join(all_levels_data_strings)
        final_dart_content += ",\n"
    final_dart_content += "];\n"

    # S'assurer que le répertoire de sortie existe
    output_dir = os.path.dirname(DART_OUTPUT_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Création du répertoire: {output_dir}")
    
    print("\n" + "="*50)
    print("RÉSULTAT DU CODE DART GÉNÉRÉ")
    print("="*50)
    print(final_dart_content)
    
    with open(DART_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_dart_content)
        
    print("\n" + "="*50)
    print(f"✅ Le script a terminé. Le résultat a été exporté dans '{DART_OUTPUT_FILE}'.")


if __name__ == "__main__":
    generate_dart_code()
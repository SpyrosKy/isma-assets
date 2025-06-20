
import os
import cv2
import numpy as np
import json

def create_flood_fill_assets(image_path, output_folder, num_clusters=16):
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error reading {image_path}")
        return None

    h, w = img.shape[:2]

    # --- 1. Create Outline Image (4-channel RGBA with transparent background) ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary_outline_inv = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    # Create a 4-channel image, fully transparent
    outline_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    # Make pixels black and opaque where the outline exists
    outline_rgba[binary_outline_inv == 255] = [0, 0, 0, 255]

    # --- 2. Create Color Mask (3-channel BGR) using KMeans Segmentation ---
    pixel_values = img.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(
        pixel_values, num_clusters, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    centers = np.uint8(centers)
    labels_reshaped = labels.reshape((h, w))

    # Create a clean mask where each segment is a solid color from the k-means centers
    segmented_color_mask = centers[labels.flatten()].reshape(img.shape)

    # --- 3. Refine: Filter unwanted regions and draw numbers on the outline ---
    unique_labels, counts = np.unique(labels, return_counts=True)
    background_candidate_label = unique_labels[np.argmax(counts)]
    
    processed_centroids_for_numbers = []
    current_region_id = 1

    for label_idx in unique_labels:
        center_color_bgr = centers[label_idx]

        # Skip likely background, very dark, or very white regions
        if (label_idx == background_candidate_label and np.mean(center_color_bgr) > 230) or \
           (np.mean(center_color_bgr) < 35) or \
           (np.mean(center_color_bgr) > 235):
            # This region is considered non-colorable, so we "erase" it from the mask
            # by setting its color to pure white, a common background color.
            segmented_color_mask[labels_reshaped == label_idx] = [255, 255, 255]
            continue

        # This is a valid, colorable region. Find where to draw its number.
        segment_mask_binary = (labels_reshaped == label_idx).astype(np.uint8)
        contours, _ = cv2.findContours(segment_mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours: continue

        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 20]
        if not valid_contours: valid_contours = contours
        
        largest_contour = max(valid_contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            can_place = True
            for prev_cx, prev_cy in processed_centroids_for_numbers:
                if np.hypot(cX - prev_cx, cY - prev_cy) < 25:
                    can_place = False
                    break
            
            if can_place:
                processed_centroids_for_numbers.append((cX, cY))
                # Draw number on the transparent outline image
                cv2.circle(outline_rgba, (cX, cY), 12, (255, 255, 255, 255), -1) # White, opaque circle
                text = str(current_region_id)
                font_scale = 0.6
                thickness = 1
                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                cv2.putText(outline_rgba, text, (cX - text_w // 2, cY + text_h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0, 255), thickness) # Black, opaque text
        
        current_region_id += 1

    # --- 4. Save the assets ---
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Save the 3-channel BGR color mask for flood fill
    cv2.imwrite(os.path.join(output_folder, f"mask_{base_name}.png"), segmented_color_mask)

    # Save the 4-channel RGBA outline with numbers and transparent background
    cv2.imwrite(os.path.join(output_folder, f"outline_{base_name}.png"), outline_rgba)

    print(f"✅ {base_name}: {current_region_id - 1} colorable regions processed.")
    return base_name

def main():
    input_dir = os.path.join(os.path.dirname(__file__), "input")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    manifest = []

    for file in os.listdir(input_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(input_dir, file)
            page_id = create_flood_fill_assets(path, output_dir)
            if page_id:
                manifest.append(page_id)

    # Use the same manifest name as before for compatibility
    with open(os.path.join(output_dir, "coloring_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"\n📄 coloring_manifest.json created with {len(manifest)} pages.")

if __name__ == "__main__":
    main()

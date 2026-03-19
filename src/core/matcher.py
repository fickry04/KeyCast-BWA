import os
import cv2
import numpy as np
# =============================================================================
# MULTI-SCALE TEMPLATE MATCHING
# =============================================================================

class MultiScaleTemplateMatcher:
    def __init__(self, scale_factors=None):
        self.scale_factors = scale_factors or [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]
        self.templates = {}
        
    def load_templates(self, folder):
        if not os.path.exists(folder):
            return 0
        self.templates = {}
        count = 0
        
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                letter = os.path.splitext(filename)[0].upper()
                if len(letter) >= 1 and letter[0].isalpha():
                    letter = letter[0]
                    filepath = os.path.join(folder, filename)
                    template = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
                    
                    if template is not None:
                        h, w = template.shape
                        scaled_versions = self._create_scaled_templates(template)
                        self.templates[letter] = {
                            'original': template, 'width': w, 'height': h, 'scaled': scaled_versions
                        }
                        count += 1
        return count
        
    def _create_scaled_templates(self, template):
        scaled = []
        h, w = template.shape
        for scale in self.scale_factors:
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w >= 5 and new_h >= 5:
                resized = cv2.resize(template, (new_w, new_h))
                scaled.append((scale, resized, new_w, new_h))
        return scaled
        
    def match(self, image_gray, threshold=0.75, min_distance=15):
        if len(image_gray.shape) == 3:
            gray = cv2.cvtColor(image_gray, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_gray
            
        detected = {}
        
        for letter, template_data in self.templates.items():
            letter_detections = []
            for scale, scaled_template, tw, th in template_data['scaled']:
                if tw > gray.shape[1] or th > gray.shape[0]:
                    continue
                    
                result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= threshold)
                
                for pt in zip(*locations[::-1]):
                    score = result[pt[1], pt[0]]
                    center_x = pt[0] + tw // 2
                    center_y = pt[1] + th // 2
                    letter_detections.append((center_x, center_y, tw, th, score))
                    
            if letter_detections:
                letter_detections = self._non_max_suppression_scored(letter_detections, min_distance)
                detected[letter] = [(x, y, w, h) for x, y, w, h, s in letter_detections]
                
        return detected
        
    def _non_max_suppression_scored(self, detections, min_distance):
        if not detections: return []
        detections = sorted(detections, key=lambda d: d[4], reverse=True)
        filtered = []
        for det in detections:
            x, y, w, h, score = det
            is_duplicate = False
            for existing in filtered:
                ex, ey, ew, eh, es = existing
                dist = np.sqrt((x - ex)**2 + (y - ey)**2)
                if dist < min_distance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered.append(det)
        return filtered

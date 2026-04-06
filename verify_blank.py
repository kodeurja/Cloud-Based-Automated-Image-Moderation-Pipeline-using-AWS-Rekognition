import boto3
import sys

def analyze_image_rekognition(file_path):
    rekognition = boto3.client('rekognition', region_name='us-east-1')
    try:
        with open(file_path, 'rb') as image:
            file_bytes = image.read()
            
        mod_response = rekognition.detect_moderation_labels(Image={'Bytes': file_bytes})
        mod_labels = mod_response.get('ModerationLabels', [])
        
        gen_response = rekognition.detect_labels(Image={'Bytes': file_bytes}, MaxLabels=10)
        gen_labels = gen_response.get('Labels', [])
        
        # PRODUCTION VERSION 1.0.3 LOGIC
        THRESHOLD = 85.0
        generic_terms = {
            "Rectangle", "Square", "Shape", "Paper", "Empty", "Void", 
            "Minimalist", "White", "Black", "Background", "Grey", "Gray", "Light",
            "Cutlery", "Racket", "Rifle", "Fork", "Tie", "Text", "Drawing", "Pattern"
        }
        
        meaningful_labels = [l for l in gen_labels if l['Confidence'] >= THRESHOLD and l['Name'] not in generic_terms]
        
        is_blank = False
        if len(mod_labels) == 0:
            if len(gen_labels) == 0:
                is_blank = True
            elif not meaningful_labels:
                is_blank = True
                
        print(f"\n--- Production v1.0.3 Result for {file_path} ---")
        print(f"Meaningful Labels (>85%): {[l['Name'] for l in meaningful_labels]}")
        print(f"IS_BLANK: {is_blank}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_image_rekognition("white_test.png")
    analyze_image_rekognition("black_test.png")

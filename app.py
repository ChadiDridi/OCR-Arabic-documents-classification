from flask import Flask, render_template, request, jsonify
from pdf2image import convert_from_path
import cv2
import pytesseract
import os
import shutil
import re
from collections import Counter
from flask import request, redirect, url_for

app = Flask(__name__, template_folder='')

def noise_removal(image):
    import numpy as np
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return image

def classify_text(text, labels):
    for label in labels:
        if label in text:
            return label
    return "OtherLabel"

def process_pdf(pdf_file):
    base_directory = "temp/"
    pdf_file_path = os.path.join(base_directory, pdf_file.filename)
    pdf_file.save(pdf_file_path)
    liste = convert_from_path(pdf_file_path, 500, poppler_path='C:\\Program Files (x86)\\poppler-23.11.0\\Library\\bin')
    listet = []
    for i, img in enumerate(liste):
        img_path = os.path.join(base_directory, f'page{i}.png')
        img.save(img_path, 'PNG')
        listet.append(img_path)
    return listet, base_directory, pdf_file_path  

def ocr_and_classification(listet, base_directory):
    ocr_result = ""
    direct = ""
    for img_path in listet:
        img = cv2.imread(img_path)
        no_noise_png = noise_removal(img)
        no_noise_path = os.path.join(base_directory, f'no_noise_{os.path.basename(img_path)}')
        cv2.imwrite(no_noise_path, no_noise_png)
        ocr_result += pytesseract.image_to_string(no_noise_path, lang='ara')

    with open(os.path.join(base_directory, "ocr_result.txt"), "w", encoding="utf-8") as file:
        file.write(ocr_result)

    label_file_path = os.path.join(direct, "label.txt")
    with open(label_file_path, "r", encoding="utf-8") as file:
        labels = [label.strip() for label in file.readlines()]

    label = classify_text(ocr_result, labels)

    return label, ocr_result, labels
def label_exists(new_label, label_file_path):
    with open(label_file_path, "r", encoding="utf-8") as file:
        labels = [label.strip() for label in file.readlines()]
        return new_label in labels
@app.route('/')
def index():
    _, _, labels = ocr_and_classification([], "")  # Get labels without processing PDF
    return render_template('index.html', label=None, labels=labels)
@app.route('/add_label', methods=['POST'])



@app.route('/add_label', methods=['POST'])
def add_label():
    new_label = request.form['new_label']
    label_file_path = os.path.join("", "label.txt")

    if label_exists(new_label, label_file_path):
            return redirect(url_for('index'))

    else:
        # Label doesn't exist, add it to the file
        with open(label_file_path, "a", encoding="utf-8") as file:
            file.write("\n")
            file.write(f"{new_label}\n")

    return redirect(url_for('index'))

@app.route('/delete_label', methods=['POST'])
def delete_label():
    label_to_delete = request.form['delete_label'].strip()  # Strip whitespace from label_to_delete
    label_file_path = os.path.join("", "label.txt")

    with open(label_file_path, "r", encoding="utf-8") as file:
        labels = [label.strip() for label in file.readlines()]

    try:
        labels.remove(label_to_delete)
    except ValueError:
        pass

    with open(label_file_path, "w", encoding="utf-8") as file:
        file.write('\n'.join(labels))

    return redirect(url_for('index'))

@app.route('/insert', methods=['POST'])
def insert():
    pdf_file = request.files['pdf']  

    try:
        
        listet, base_directory, pdf_file_path = process_pdf(pdf_file)
        label, ocr_result, labels = ocr_and_classification(listet, base_directory)
        pdf_filename = ""
        if label != "OtherLabel":
            pdf_filename = os.path.basename(pdf_file_path)
            destination_directory = os.path.join("", label)
            os.makedirs(destination_directory, exist_ok=True)
            shutil.copy(pdf_file_path, os.path.join(destination_directory, pdf_filename))  # Copy the original PDF
            shutil.copy(os.path.join(base_directory, "ocr_result.txt"), os.path.join(destination_directory, label+".txt"))
            print(f"File successfully classified and moved to {label} directory.")
        else:
            pdf_filename = os.path.basename(pdf_file_path)
            linkers = ["من", ".", "و", ".", "حتى", ".", "في", "."]
            words = re.findall(r'\b\w+\b', ocr_result)
            word_counts = Counter(word for word in words if word not in linkers)

            most_common_word, most_common_count = word_counts.most_common(1)[0]

            total_words = len(words) 
            percentage = (most_common_count / total_words) * 100

            destination_directory = os.path.join("", most_common_word)
            os.makedirs(destination_directory, exist_ok=True)
            with open(os.path.join(destination_directory, f"{most_common_word}.txt"), "w", encoding="utf-8") as output_file:
                shutil.copy(os.path.join(base_directory, "ocr_result.txt"), os.path.join(destination_directory, f"{most_common_word}.txt"))
                print(f"File successfully classified and moved to {most_common_word} directory.")
            shutil.copy(pdf_file_path, os.path.join(destination_directory, pdf_filename))  # Copy the original PDF
            label = most_common_word
            label_file_path = "label.txt"
            with open(label_file_path, "a", encoding="utf-8") as file:
                file.write(f"\n{most_common_word}")
        return jsonify({'label': label, 'labels': labels})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

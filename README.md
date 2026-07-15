<div align="center">

# 📄 Smart OMR Data Capture and Excel Synchronization System

### Intelligent Computer Vision-Based OMR Evaluation and Excel Reporting System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv)
![NumPy](https://img.shields.io/badge/NumPy-Scientific-orange?logo=numpy)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel-success)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue)
![Status](https://img.shields.io/badge/Project-Completed-brightgreen)

</div>

---

## 📖 Overview

Smart OMR Data Capture and Excel Synchronization System is an image-processing application that automates the evaluation of Optical Mark Recognition (OMR) sheets. The system detects filled bubbles from scanned images using OpenCV and exports the extracted responses directly into Microsoft Excel.

Unlike traditional OMR systems, this solution works with ordinary scanned images or mobile camera images without requiring expensive OMR scanners.

---

# 📑 Table of Contents

- Problem Statement
- Solution Overview
- Key Features
- System Architecture
- Technology Stack
- Algorithms Used
- Workflow
- Installation
- Usage
- Project Structure
- Output
- Future Enhancements

---

# ❓ Problem Statement

Traditional OMR systems require specialized hardware and commercial software, making them expensive and inaccessible for many educational institutions. Manual evaluation is time-consuming and prone to human errors. There is a need for an automated, accurate, and cost-effective solution capable of processing multiple OMR sheets efficiently.

---

# 💡 Solution Overview

The proposed system automates the complete OMR evaluation process.

- Reads OMR sheet images from a folder.
- Performs image preprocessing.
- Detects answer bubbles automatically.
- Identifies selected options.
- Generates Excel reports automatically.
- Supports bulk image processing.

---

# ✨ Key Features

- 📂 Bulk OMR Processing
- 🎯 Automatic Bubble Detection
- 📷 Works with Scanner or Mobile Camera Images
- 📊 Excel Report Generation
- 🖥️ Interactive Preview
- ⚡ High-Speed Processing
- 🎨 Template-Based Detection

---

# 🏗️ System Architecture

```
OMR Images
     │
     ▼
Image Acquisition
     │
     ▼
Image Preprocessing
     │
     ▼
Bubble Detection
     │
     ▼
Answer Recognition
     │
     ▼
Excel Generation
```

---

# 💻 Technology Stack

| Category | Technology |
|-----------|------------|
| Programming Language | Python |
| Computer Vision | OpenCV |
| Numerical Computing | NumPy |
| Excel Processing | OpenPyXL |
| GUI | Tkinter |

---

# 🧠 Algorithms Used

- Grayscale Conversion
- Gaussian Blur
- Otsu Thresholding
- Hough Circle Transform
- Contour Detection
- Fill Ratio Analysis
- Adaptive Bubble Detection

---

# 🔄 Workflow

1. Select image folder.
2. Choose template image.
3. Select bubble regions.
4. Detect circles.
5. Calculate bubble fill ratio.
6. Identify marked answers.
7. Preview results.
8. Export to Excel.

---

# 📦 Installation

```bash
git clone https://github.com/yourusername/Smart-OMR-System.git

cd Smart-OMR-System

pip install -r requirements.txt

python omr_bulk_folder_processor.py
```

---

# 📂 Project Structure

```
Smart-OMR-System/
│
├── omr_bulk_folder_processor.py
├── sample_images/
├── output/
├── README.md
├── requirements.txt
└── screenshots/
```

---

# 📸 Sample Output

### Input
- Scanned OMR Sheet

### Output
- Detected Answers
- Excel Report

---

# 🚀 Future Enhancements

- Automatic Template Detection
- Machine Learning-based Recognition
- PDF Result Generation
- Web Dashboard
- Cloud Storage
- Mobile Application Support

---

# 👩‍💻 Author

**Junugari Laharika**

Bachelor of Technology (Computer Science and Engineering)

---

## ⭐ If you found this project useful, consider giving it a Star!

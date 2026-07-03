📄 OMR Sheet Evaluation System (OMR → Excel)
📌 Project Overview

This project is a computer vision–based OMR (Optical Mark Recognition) system that automatically reads bubbled answers from OMR sheets and records the results into an Excel file.

Unlike traditional OMR machines, this system works using image processing techniques and can process:

Scanned OMR sheets

Camera-captured images

Multiple sheets in bulk (folder input)

The system requires the OMR template to be defined once, after which the same template is applied to all other OMR images.

🎯 Objectives

Automate detection of bubbled answers in OMR sheets

Convert OMR responses into structured Excel format

Eliminate manual data entry

Provide a low-cost, software-based alternative to OMR machines

✅ Key Features

📂 Bulk Processing: Scan all OMR images in a selected folder

✂️ Template Training: Crop OMR bubble regions on the first image only

🔁 Template Reuse: Same template applied to all images automatically

🎯 Accurate Bubble Detection:

Detects filled, unfilled, and multiple filled options

Handles cases where all options are bubbled

👀 Interactive Preview:

Navigate detected results using Next / Previous

Visual confirmation of detected bubbles

📊 Excel Output:

One Excel sheet for all images

Separate columns for each OMR sheet

🛠 Technologies Used

Python

OpenCV – Image processing

NumPy – Numerical operations

Tkinter – File & folder selection dialogs

OpenPyXL – Excel file generation

🗂 Project Structure
omr-bulk-evaluator/
│
├── omr_bulk_folder_processor.py   # Main program
├── README.md                      # Project documentation
└── omr_bulk_results.xlsx          # Generated output (after running)

⚙️ Installation & Setup
1️⃣ Install Python

Make sure Python 3.8 or above is installed.

Check using:

python --version

2️⃣ Install Required Libraries
pip install opencv-python numpy openpyxl


⚠️ tkinter usually comes pre-installed with Python.

▶️ How to Run the Project
Step 1: Run the program
python omr_bulk_folder_processor.py

Step 2: Select OMR Images Folder

Choose a folder containing all OMR images

All images must follow the same OMR template

Step 3: Select Template Image

Select one OMR image to define the template

This image is used only for:

Selecting bubble regions

Learning bubble positions

Step 4: Crop Bubble Regions

Select only the bubble areas

Avoid question numbers or text

You can select multiple regions

Press ESC when finished

Step 5: Automatic Evaluation

The system:

Detects bubbles

Identifies filled options

Processes all images in the folder

Step 6: Preview Results

Navigate images using:

Next / Previous buttons

Keyboard shortcuts: n (next), p (previous)

Press:

s to save Excel file

q to quit without saving

Step 7: Excel Output

An Excel file named:

omr_bulk_results.xlsx


will be generated with the format:

S.No (Image1)	Option (Image1)	S.No (Image2)	Option (Image2)	...
📌 Bubble Detection Logic

Each bubble is analyzed using pixel intensity

A bubble is considered filled if:

A significant portion of pixels inside the circle are dark

Supports:

No filled bubbles → -

One filled bubble → A / B / C / D

Multiple filled bubbles → A,B etc.

⚠️ Limitations

Works best with clean scanned images

Camera images require:

Good lighting

Minimal skew

Template must be consistent across all images

This project does not aim for commercial-grade accuracy

🔮 Future Improvements

Support for PDF input

Automatic sheet alignment correction

Roll number recognition

Web-based interface

Confidence score per answer

👨‍💻 Author

Developed as an academic mini-project to demonstrate practical application of:

Computer Vision

Image Processing

Automation

⭐ Acknowledgement

Inspired by traditional OMR evaluation systems and implemented using open-source tools.

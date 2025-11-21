# GDELT Helper
A user-friendly **GUI application for downloading, filtering, and exporting GDELT event data**.  
Designed for researchers who need efficient access to GDELT’s large-scale event dataset without writing code.

> **Note:**  
> The current GUI interface is in **Traditional Chinese**,  
> but the layout is intuitive (mode selection, folder selection, year range, start, stop),  
> and can be operated easily by non-Chinese users.

---

## Table of Contents
- [Introduction](#introduction)
- [System Requirements](#system-requirements)
- [Main Interface](#main-interface)
- [Modes & Features](#modes--features)
  - [Download Mode](#1-download-mode)
  - [Data Processing Mode](#2-data-processing-mode)
  - [Notification Settings](#3-notification-settings)
- [Installation & Usage](#installation--usage)
- [Data Source & Citation](#data-source--citation)
- [License](#license)
- [Author](#author)

---

## Introduction

The GDELT dataset is extremely large and complex to manage manually. 
As of **September 20, 2025**, the database contains:

- **4,718 files**
- **~268 GB** of uncompressed data

To reduce the technical burden for researchers, **GDELT Helper** automates:

- Downloading  
- Unzipping  
- Filtering by fields, actors, countries, actor types  
- Selecting year ranges  
- Exporting data to CSV, DAT, SAV, TSV, etc.  

This tool provides a GUI-based workflow so researchers can process GDELT data efficiently without programming.

---

## System Requirements

- **Operating System:** Windows 10 or later  
- **RAM:** Recommended 8 GB or above (tested peak usage: ~7 GB)  
- **Disk Space:** Depends on selected data range  
- **Software**
  - Python 3.10+  
  - or packaged `GDELT_helper.exe` (Windows only)

---

## Main Interface

When the application launches, the main window appears with the primary navigation on the left.  
The application consists of **three major modules**:

1. **Download Mode**  
2. **Data Processing Mode**  
3. **Email Notification Settings**

---

## Modes & Features

### **1. Download Mode**

This mode allows users to automatically download single or multiple years of GDELT data.

Key features:

1. **Download directory selection**  
   Choose where raw GDELT data will be stored.  
   If files for a selected year already exist, the program will automatically skip them.

2. **Detect available years**  
   If your local folder lacks certain years, click “Detect Latest Year” to update the year list.

3. **Year selection**  
   - Select all years at once  
   - Drag to select continuous years  
   - Hold **Ctrl** to select non-contiguous years

4. **Download log**  
   Real-time messages showing success, skipped files, errors, and progress.

---

### **2. Data Processing Mode**

This mode provides structured filtering and exporting functions for researchers.

Main functions:

1. **Input & Output Settings**  
   - Select raw data source folder  
   - Select output folder  
   - Type desired output filename  
   - Export format is based on extension (e.g., `.csv`, `.tsv`, `.dat`, `.sav`)  
     - Recommended formats: CSV or TSV

2. **Field Selection (Variable Filtering)**  
   Select variables to keep in the output file.  
   Hold **Ctrl** to multi-select.  
   **You must click “Apply”** after selecting variables, otherwise defaults remain.

   Default included variables:
   - SQLDATE  
   - MonthYear  
   - Year  
   - Actor1CountryCode  
   - Actor1Type1Code  
   - Actor2CountryCode  
   - Actor2Type1Code  
   - IsRootEvent  
   - EventCode  
   - EventBaseCode  
   - QuadClass  
   - GoldsteinScale
   - AvgTone

3. **Country Filtering (ISO3)**  
   - Separate filters for Actor 1 and Actor 2  
   - Enter multiple ISO3 codes separated by commas  
   - Quick-select common countries  
   - Option: **Keep only records where A1 and A2 are different countries**  
   - This application uses **ISO 3166-1 alpha-3 (ISO3C)** country codes.
     For a comprehensive list of ISO3 country codes, see the official **CAMEO Conflict and Mediation Event Observations Event and Actor Codebook (pp. 168)**:  
     http://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf
     
   > **Note:**  
   > GDELT does not include event records for certain ISO3 countries.  
   > For example, **Slovenia (SVN)** does not appear at all in the original GDELT raw files.  
   > This absence reflects the underlying GDELT dataset (i.e., no recorded events for that country),  
   > not a limitation or error of this application.

4. **Year Range Filtering**  
   Specify start year and end year.  
   Example: Setting 2005–2023 includes **all data up to 2023/12/31**.

5. **Actor Type Filtering (CAMEO ActorType Codes)**  
   - Separate filters for Actor1 and Actor2  
   - Examples: GOV, MIL, COP, JUD, OPP, REB, etc.  
   - Option:  
     - Keep **all** data  
     - or keep **only data with actor-type labels**  
   - For a comprehensive list of CAMEO ActorType Codes, see the official **CAMEO Conflict and Mediation Event Observations Event and Actor Codebook (pp. 93)**:  
     http://data.gdeltproject.org/documentation/CAMEO.Manual.1.1b3.pdf
     
---

### **3. Notification Settings**

Allows automated email alerts when long downloads or data processing tasks are completed.

Features:

1. **Enable notification**  
   - Optional setting(must be checked if you wish to use the notification feature)

2. **SMTP server settings**  
   - Example for Gmail:  
     - Host: `smtp.gmail.com`  
     - Port: `587`

3. **Sender & Recipient Information**  
   - Sender account and password  
   - Gmail users must use an **App Password**  
   - Multiple recipients separated by commas

4. **Send Test Email**  
   Recommended before running large tasks.

---


## Installation & Usage

### **Option 1: Use the Windows Executable (`GDELT_helper.exe`)**

No Python installation needed.

1. Download from **Releases**  
2. Extract the ZIP  
3. Run:
```
GDELT_helper.exe
```
### **Option 2: Run from Python Source Code**

1. Install Python **3.10+**
2. Install required dependencies:
```bash
pip install -r requirements.txt
```
3. Launch the application:
```bash
python main.py
```

---

## Data Source & Citation
This tool downloads and processes data from:

The GDELT Project — Global Database of Events, Language, and Tone
https://www.gdeltproject.org/

If you use this tool or GDELT data in academic work, please cite:

The GDELT Project. Global Database of Events, Language, and Tone (GDELT).

This application is an independent third-party tool and is
not affiliated with or endorsed by The GDELT Project.

---

## License

Released under the MIT License.
You may modify or distribute under the terms of this license.

---

## Author
Hong Zih-Chun (洪子淳)
Graduate Institute of East Asian Studies  
National Chengchi University (NCCU), Taiwan

---

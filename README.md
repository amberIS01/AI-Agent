# 🏥 Hospital Reimbursement Portal

A Streamlit web application for searching and viewing hospital reimbursement information from Excel files.

## ✨ Features

- Modern, responsive web interface
- Search across procedure names, codes, and descriptions
- Quick question suggestions
- Detailed procedure information display
- Documentation requirements and exceptions
- Mobile-friendly design

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone this repository or download the source code
2. Navigate to the project directory:
   ```bash
   cd hospital_reimbursement_bot
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Place your Excel files in the `data` folder
2. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

## 🖥️ Usage

1. **Search Bar**
   - Type your question in the main search box
   - Use the checkbox to toggle fuzzy search (helps with typos)
   - Click "Search" or press Enter

2. **Quick Questions**
   - Use the sidebar to select from common queries
   - Click any question to automatically search

3. **Viewing Results**
   - Results are displayed in clean, organized cards
   - Expand sections to see documentation requirements and exceptions
   - View procedure details including codes and amounts

## 📁 Project Structure

```
hospital_reimbursement_bot/
├── data/                   # Folder containing Excel files
├── app.py                 # Streamlit web application
├── bot.py                 # Core bot functionality
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🛠️ Customization

1. **Data**
   - Add Excel files to the `data` directory
   - The app will automatically load all Excel files

2. **Styling**
   - Modify the CSS in `app.py` to change colors and layout
   - Update the color scheme in the `set_page_config` section

3. **Search Logic**
   - Customize search behavior in `bot.py`
   - Modify the `search` method for different result rankings

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 📞 Support

For support or feature requests, please open an issue in the repository.

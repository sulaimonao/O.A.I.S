
# **O.A.I.S.**

![O.A.I.S.](backend/static/img/logo.png)

**O.A.I.S.** is a comprehensive framework for...

### Key Features
- **AI-Powered Task Execution:** Execute complex tasks using state-of-the-art AI models.
- **Custom Model Integration:** Easily integrate local models like GPT-2 for task execution and system analysis.
- **Memory Management:** Manage system memory and toggle features for privacy and user control.

---

### **Setup Instructions**

#### **1. Clone the Repository:**
```bash
git clone https://github.com/sulaimonao/O.A.I.S.git
```

#### **2. Install Dependencies:**
```bash
pip install -r requirements.txt
```

#### **3. Set up Environment Variables:**
Create a `.env` file in the root directory and populate it with your API keys and environment variables.
Example:
```bash
OPENAI_API_KEY=your_openai_api_key
```

#### **4. Run the Application:**
```bash
python main.py
```

The application will launch with the default provider and engine. **Important:** Default settings will not be saved until you manually change them in the application and click "Save."

---

### **Usage Guide**

1. **Customizing Providers and Engines:**
   - Use the application interface to select your preferred provider and engine.
   - Click "Save" to apply and register the changes.

2. **Debugging:**
   - If you encounter issues, check the log files located in the `/logs` directory.
   - To troubleshoot memory-related issues, toggle the memory feature from the user interface and observe changes in system behavior.


---

### **Contributing**

Feel free to contribute by submitting your ideas to "Open Issues"

---

### **Requirements**

Check the `requirements.txt` file for all necessary dependencies.

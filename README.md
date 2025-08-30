# 🎨 SVG Gradient CrewAI  

**Natural language powered SVG gradient generator using CrewAI agents.**  

This project converts plain English instructions into valid **SVG gradient modifications** using a multi-agent workflow. It demonstrates how AI agents can parse, modify, and validate design specifications, bridging the gap between **natural language** and **structured SVG updates**.

---

## 🚀 Features  
- Accepts **natural language prompts**.  
- Runs **CrewAI agents** to parse, modify, and validate SVGs.  
- Supports **linear, radial, vertical, horizontal, and diagonal gradients**.  
- Identifies SVG elements by **id, class, or tag** (`circle`, `rect`, etc.).  
- Provides **detailed logs** of parsing, modification, and validation steps.  
- Generates **before & after SVG snippets** in the console.  
- **Bonus:** LLM-enabled mode (`ENABLE_LLM=1`) for advanced parsing when API key is valid.  

---

## 📦 Deliverables  
- A Python script (`main.py`) that:  
  - Accepts a natural language prompt.  
  - Runs CrewAI agents to update the SVG accordingly.  
  - Outputs a valid `output.svg`.  

- Print/log the workflow:  
  - User prompt.  
  - Parsed gradient config.  
  - Actions by each agent.  

- Includes:  
  - **Before and after SVG snippets**.  
  - **Comments explaining agent roles and logic** inside the code.  

---

## 🛠️ Installation  

Clone the repository and install dependencies:  

```bash
git clone https://github.com/Naitik2302/svg-gradient-crewai.git
cd svg-gradient-crewai
pip install -r requirements.txt
python main.py

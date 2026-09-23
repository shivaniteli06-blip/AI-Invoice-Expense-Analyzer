# AI Invoice & Expense Analyzer

A **multi-agent AI application** that helps individuals and small organizations understand their spending through intelligent, automated expense analysis — built with Python, Streamlit, and the Groq API.

---

## 📋 Problem Statement

Individuals and small organizations often have expense information spread across invoices, bills, receipts, CSV files, and manual records. It can be difficult to:
- Understand where most money is spent
- Know which categories dominate their budget
- Identify unusual or anomalous transactions
- Compare spending against predefined budgets
- Get actionable insights in simple language

This application solves all of these problems through a live, animated multi-agent AI pipeline.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Pipeline** | 5 specialized AI agents run sequentially and visibly in real time |
| **Live Pipeline Animation** | Watch each agent activate, process, and complete with animated nodes |
| **Expense Extraction** | Parse natural language, invoices, CSV files, and PDF documents |
| **Smart Classification** | AI categorizes transactions into 11 spending categories |
| **Spending Analysis** | Python-computed statistics with AI plain-language explanations |
| **Anomaly Detection** | Z-score based flagging of unusual transactions, explained by AI |
| **Budget Analysis** | Compare spending against user-defined budgets per category |
| **AI Expense Assistant** | Chat interface with streaming responses about your spending |
| **Interactive Charts** | Plotly charts: donut, area timeline, grouped bar, scatter, horizontal bars |
| **Animated UI** | Count-up metric cards, fade-in sections, progress bars, dark mode |
| **Reports & Export** | Full analysis report with CSV and text download options |

---

## 🤖 Multi-Agent Architecture

Five specialized agents cooperate **sequentially** — each receives the previous agent's output:

```
USER INPUT
    ↓
🔍 Agent 1: Extraction Agent
   └─ Parses raw text/files into structured transaction records
    ↓
🏷️ Agent 2: Classification Agent
   └─ Categorizes each transaction (Food, Travel, Utilities, etc.)
    ↓
📊 Agent 3: Analysis Agent
   └─ Python computes stats; Groq explains them in plain language
    ↓
⚠️ Agent 4: Anomaly Detection Agent
   └─ Python flags unusual transactions; Groq explains cautiously
    ↓
💰 Agent 5: Budget Advisory Agent
   └─ Compares actual vs. budget; Groq gives practical advice
    ↓
📊 FINAL DASHBOARD + REPORT
```

**Key principle:** All arithmetic is performed in Python (pandas). The LLM only provides natural-language explanations of pre-computed results — never recalculates numbers.

---

## 🛠️ Technology Stack

- **Python 3.10+** — Core language
- **Streamlit** — Web UI with custom CSS/HTML/JS animations
- **Groq API** — Fast LLM inference (`llama-3.3-70b-versatile`)
- **Pandas** — All numerical calculations
- **Plotly** — Interactive, animated charts
- **PyMuPDF** — PDF text extraction
- **python-dotenv** — Environment variable management

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI_Invoice_Expense_Analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Groq API Key

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
# Get your key from: https://console.groq.com
```

`.env` file:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 4. Run the application

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 📊 How to Use

### Loading Expenses

**Option 1 — Sample Data:** Click "Load Sample Data" on the Dashboard or Upload page. The app includes 30+ fictional transactions including an intentionally unusual ₹8,500 food expense for anomaly demonstration.

**Option 2 — Manual Entry:** Go to "Add Expenses" → "Manual Entry" and fill in the form.

**Option 3 — CSV Upload:** Go to "Upload Expenses" → "CSV Upload" and upload a file with columns: `date, merchant, description, amount, category, payment_method`

**Option 4 — Text Input:** Go to "Add Expenses" → "Text Input" and paste natural language like: *"Yesterday I spent ₹850 at ABC Restaurant and ₹450 on Uber."*

**Option 5 — Invoice Upload:** Go to "Upload Expenses" → "Invoice/Document" and upload a text-based PDF or TXT file.

---

## ⚠️ How Anomaly Detection Works

1. **Python Z-score analysis**: For each expense category, the app calculates the mean and standard deviation of historical amounts.
2. **Flagging**: Any transaction with a Z-score > 2.0 (more than 2 standard deviations above the category mean) is flagged.
3. **AI Explanation**: Groq explains flagged transactions using cautious language ("Potential anomaly", "Requires verification") — never "fraudulent".

**Demo scenario**: The sample data includes an ₹8,500 food expense. With food transactions typically ranging ₹480–₹700, this is flagged as a potential anomaly (~6× the category average).

---

## 💰 How Budget Analysis Works

1. Go to "Budget Analysis" and expand "Configure Budgets"
2. Set monthly budget amounts per category
3. Click "Save Budgets"
4. The app computes: budget amount, amount spent, remaining, % utilized, and over-budget amount
5. Color-coded progress bars show utilization (green < 80%, yellow 80–100%, red > 100%)
6. Groq provides practical, actionable feedback per category

---

## 📁 Project Structure

```
AI_Invoice_Expense_Analyzer/
│
├── app.py                      # Main Streamlit application
│
├── agents/
│   ├── extraction_agent.py     # Agent 1: Parse raw text → structured data
│   ├── classification_agent.py # Agent 2: Categorize transactions
│   ├── analysis_agent.py       # Agent 3: Compute + explain spending stats
│   ├── anomaly_agent.py        # Agent 4: Detect + explain anomalies
│   └── budget_agent.py         # Agent 5: Compare vs. budgets + advice
│
├── utils/
│   ├── groq_client.py          # Groq API client (call + stream)
│   ├── calculations.py         # All Python arithmetic (no LLM math)
│   ├── data_loader.py          # CSV loading and data normalization
│   └── file_parser.py          # PDF/TXT file parsing
│
├── ui/
│   ├── theme.py                # CSS variables, light/dark mode, fonts
│   ├── animations.py           # CSS keyframes and animation helpers
│   ├── components.py           # Metric cards, pipeline visualizer, badges
│   └── charts.py               # Plotly chart builders
│
├── prompts/
│   └── agent_prompts.py        # All LLM prompt templates
│
├── data/
│   └── sample_expenses.csv     # 30+ fictional sample transactions
│
├── .env.example                # API key template
├── requirements.txt
└── README.md
```

---

## 🔄 Example Workflow

```
1. Load sample_expenses.csv (30 transactions)
2. Pipeline runs:
   🔍 Extraction Agent  → "30 transactions loaded"
   🏷️ Classification → "Food: 10, Travel: 4, Utilities: 4..."
   📊 Analysis      → "Total: ₹45,800 across 30 transactions"
   ⚠️ Anomaly      → "1 potential anomaly: ₹8,500 Food expense"
   💰 Budget        → "Food budget exceeded by ₹3,500"
3. Dashboard shows animated metric cards and interactive charts
4. Ask the assistant: "What was my highest expense?"
5. Download the full report as CSV or text
```

---

## 📐 Data Integrity Rules

- ✅ All arithmetic done in Python — LLM never calculates numbers
- ✅ Missing fields explicitly marked "Not available" — never invented
- ✅ Anomalies described cautiously — never called "fraudulent"
- ✅ Budget advice based only on user-provided data
- ✅ AI insights clearly labeled `🤖 AI Insight` vs `🧮 Calculated`
- ✅ No financial data stored permanently — session only

---

## ⚠️ Limitations

- PDF parsing works only with text-based PDFs (not scanned images)
- Anomaly detection requires at least 2 transactions per category
- AI explanations depend on Groq API availability
- Currency defaults to INR; multi-currency support is limited
- No persistent storage — data resets on page refresh

---

## 🔒 Privacy

All financial data is processed in-session only and is never stored permanently. No data is sent to any service other than the Groq API for language model inference. Handle uploaded financial information with care.

---

## 📦 Requirements

```
streamlit>=1.32.0
groq>=0.5.0
pandas>=2.0.0
plotly>=5.18.0
python-dotenv>=1.0.0
PyMuPDF>=1.23.0
Pillow>=10.0.0
```

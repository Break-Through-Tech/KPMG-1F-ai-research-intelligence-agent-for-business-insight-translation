KPMG — AI Research Intelligence Agent for Business Insight Translation

> 💡 **Note for the team:** This is just a template. Update the above title with your AI Studio Challenge Project name. Remove all guidance notes and example text in this template and populate this README with your own content. You can work on this README throughout AI Studio, and get feedback from your AI Studio Coach and Challenge Advisor before finalizing it.  

---

### 👥 **Team Members**

| Name               | GitHub Handle | Contribution                                                             |
|------------------  |---------------|--------------------------------------------------------------------------|
| Jenna Hunte        | @jehunte      | Break Through Tech Coach                                                 |
| Alesha Rafi        | @ralesh10     | Team Member                                                              |
| Latifa Abdraimova  | @latiifkaa    | Team Member                                                              |
| Teegawende Segrado | @Teegawende12 | Team Member                                                              |
| Jooheon Lee        | @             | Team Member                                                              |
| Khoi Nguyen        | @             | Team Member                                                              |
| James Zhu          | @             | Team Member                                                              |

---

## 🎯 **Project Highlights**

**Example:**

-Building a RAG (Retrieval-Augmented Generation) agent: parse AI research papers with PyMuPDF → chunk & embed the text with OpenAI's text-embedding-3-small → store/retrieve in ChromaDB → summarize and translate findings into business implications with OpenAI gpt-4-mini, always citing the source.
-Success looks like: the system consistently retrieves relevant papers for a business question, accurately summarizes key points without losing important context, and its output (relevance, accuracy, business usefulness) holds up under KPMG stakeholder review.
-Milestone #1 (Sept 30): data exploration/preprocessing, an evaluation framework with benchmark queries, and a baseline retrieval pipeline. -Milestone #2 (Oct 31): full retrieval + summarization pipeline, business-translation prompt engineering, and initial accuracy evaluation. --Milestone #3 (Nov 30): output refinement, a lightweight UI/interaction layer, and final documentation.
Developed in partnership with KPMG as part of the Break Through Tech AI Studio program.

---

## 👩🏽‍💻 **Setup and Installation**

**Provide step-by-step instructions so someone else can run your code and reproduce your results. Depending on your setup, include:**

* How to clone the repository
* How to install dependencies
* How to set up the environment
* How to access the dataset(s)
* How to run the notebook or scripts
Python 3.10+ installed (python.org)
Git installed
VS Code (team's standard IDE), or your editor of choice
JupyterLab for exploratory data analysis and prototyping
A Google Colab account, used for cloud compute (e.g. GPUs) when needed
An OpenAI API key (for embeddings and gpt-4-mini)
1. Clone the repository

Clone the repo from GitHub to your local machine using Git, then navigate into the project folder.

2. Set up the environment

Create and activate a Python virtual environment so the project's dependencies stay isolated from other Python projects on your machine.

3. Install dependencies

Install the required packages listed in requirements.txt, which include the team's tech stack: PyMuPDF for PDF parsing, OpenAI for embeddings and the LLM, ChromaDB as the vector store, plus supporting libraries (pandas, numpy, jupyter, python-dotenv). Re-install whenever new packages are added.

4. Set up API keys / secrets

Create a .env file in the project root to store your OpenAI API key. This file is excluded from version control via .gitignore, so keys are never committed to the repo. If working in Google Colab, use Colab's built-in "Secrets" manager instead.

5. Access the dataset(s)

Place the research paper corpus (PDFs) in the data/ folder. The starting corpus is 5 public AI research papers, with an expected total size under 1GB; the team also uses Google Drive for sharing datasets and documentation.

6. Run the notebook or scripts

Open the notebooks locally in JupyterLab, or in Google Colab by opening the notebook directly from GitHub. The typical pipeline flow: parse the PDFs → clean and chunk the text → generate embeddings → store and query them in ChromaDB → retrieve relevant passages for a business question and generate a cited, business-translated answer using the LLM.

---

## 🏗️ **Project Overview**

**Describe:**

- This project is part of the Break Through Tech AI Studio program, which pairs student fellows with host companies to solve real-world AI/ML challenges.
-Host company: KPMG — a professional services firm providing audit, tax, and advisory services, helping organizations manage risk, improve operations, and make business decisions. KPMG operates globally across industries including financial services, technology, healthcare, retail, consumer goods, energy, and the public sector.
-Key stakeholders: KPMG employees and teams working with AI research and emerging technologies, plus consultants who apply these insights with clients.
-Objective and scope: Build an AI research agent (RAG pipeline) that finds relevant information in AI research articles for a given business question, summarizes it, and translates it into clear business implications or actionable tasks — with citations back to the source.
-Real-world significance: KPMG consultants and stakeholders need to stay current on AI research to advise clients, but reading and synthesizing academic papers is time-consuming. An agent that can accurately surface and translate relevant findings into business terms — with verifiable citations — could meaningfully speed up how research gets applied to client work.
---

## 📊 **Data Exploration**

Source: Public research articles about Artificial Intelligence.
-Type/format: Primarily unstructured text (PDF), and may include figures/images and numerical values; starting corpus is 5 papers, expected total size under 1GB.
-Planned EDA: examine what kinds of figures/images appear and how to extract useful information from them; check for missing or outdated information, duplicates, and papers not relevant to the project scope.
-Planned preprocessing: extract and clean text from PDFs, split into appropriately sized chunks, prepare text + metadata for retrieval, generate embeddings per chunk, and store those embeddings in the vector database (ChromaDB) for semantic similarity search.

**Potential visualizations to include:**

(Add EDA findings, visualizations, and preprocessing decisions here once that work is completed.)

---

## 🧠 **Model Development**

**You might consider describing the following (as applicable):**

* Model(s) used (e.g., CNN with transfer learning, regression models)
* Feature selection and Hyperparameter tuning strategies
* Training setup (e.g., % of data for training/validation, evaluation metric, baseline performance)


---

## 📈 **Results & Key Findings**

**You might consider describing the following (as applicable):**

* Performance metrics (e.g., Accuracy, F1 score, RMSE)
* How your model performed
* Insights from evaluating model fairness

**Potential visualizations to include:**

* Confusion matrix, precision-recall curve, feature importance plot, prediction distribution, outputs from fairness or explainability tools

---

## 🚀 **Next Steps**

**You might consider addressing the following (as applicable):**

* What are some of the limitations of your model?
* What would you do differently with more time/resources?
* What additional datasets or techniques would you explore?

---

## 📝 **License**

Specify how your project can be used by others. Choose an appropriate license and link it here (e.g., MIT, Apache 2.0). Make sure your Challenge Advisor approves of the selected license type. 

**Example:**
This project is licensed under the MIT License.

---

## 📄 **References** (Optional but encouraged)

Cite relevant papers, articles, or resources that supported your project.

---

## 🙏 **Acknowledgements** (Optional but encouraged)

Thank you to Challenge Advisor Agnieszka (AJ) Jeter and the team at KPMG, and to AI Studio Coach Jenna Hunte, for their support on this project.

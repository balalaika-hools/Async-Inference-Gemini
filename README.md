

# Async-Inference-Gemini

This project performs **structured output inference** (in JSON format) on PDF or image files using [Google's Generative AI SDK](https://googleapis.github.io/python-genai/) in combination with **Vertex AI** and **Gemini models**.

It supports:

* Parallel asynchronous inference with retry/backoff logic
* Structured output generation based on user-defined JSON schemas and prompts
* Automatic sampling and graceful error handling
* Processes both PDF and image files (`.pdf`, `.jpg`, `.png`)

---

## 📁 Project Structure

```
Arch-Async-Inference-Gemini/
├── README.md
├── config/
│   └── config.yaml                    # Configuration parameters
├── jupyter/
│   └── run_inference.ipynb            # Interactive notebook
├── pyproject.toml                    
├── misc/
│   ├── output/
│   │   └── results.json               # Inference output
│   ├── prompts/
│   │   └── prompt.yaml                # Prompt definition
│   └── schemas/
│       └── schema.json                # JSON output schema definition
├── requirements.txt                   # Project dependencies
└── scripts/
    ├── __init__.py
    ├── utils.py
    └── main.py 
```

---

## ⚙️ Configuration (`config/config.yaml`)

### 🔹 General Parameters

| Parameter       | Description |
|----------------|-------------|
| `PROJECT_ID`    | GCP Project ID used with Vertex AI |
| `LOCATION`      | Vertex AI region (e.g., `us-central1`) |
| `PDF_FOLDER_PATH` | Absolute path to the folder containing PDF or image files |
| `MODEL`        | Gemini Model version (eg. `gemini-2.5-flash`) |
| `SAMPLE`        | If `null`: process all files. If `int`: randomly sample that many files |

---

### 🔹 Request Control

| Parameter       | Description |
|----------------|-------------|
| `CONC_TASKS`    | Max number of concurrent inference requests |
| `MAX_FAILED`    | Maximum number of allowed failed requests before aborting |
| `MAX_RETRIES`   | Retry attempts per failed request (with exponential backoff) |

---

### 🔹 Cost Tracking / Tagging

These labels are passed to Vertex AI for billing and tracking purposes:

```yaml
LABELS:
  Developer: SpyrosBibilas
  Description: 'A random Test'
````

---

### 🔹 Generation Config Parameters

These control the behavior of the Gemini model during generation:

| Parameter           | Description                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------- |
| `TEMPERATURE`       | Controls randomness. Range: \[0.0, 1.0]                                                  |
| `TOP_P`             | Nucleus sampling cutoff. Range: (0.0, 1.0]                                               |
| `TOP_K`             | Top-k sampling. Range: \[1, 40]                                                          |
| `CANDIDATE_COUNT`   | Number of completions to generate                                                        |
| `SEED`              | Random seed for reproducibility                                                          |
| `MAX_OUTPUT_TOKENS` | Maximum tokens per completion                                                            |
| `PRESENCE_PENALTY`  | Penalizes repeating topics. Range: \[-2.0, 2.0]                                          |
| `FREQUENCY_PENALTY` | Penalizes repeated tokens                                                                |
| `THINKING_BUDGET`   | Experimental: see [thinking budget docs](https://ai.google.dev/gemini-api/docs/thinking) |

> 💡 Leave fields `null` to use API defaults — but it's **recommended** to set values explicitly.


---

## 🧪 Prompt and Schema Setup

You must define:

* A **prompt** in: `misc/prompts/prompt.yaml`
* A **structured output schema** in: `misc/schemas/schema.json`

> See the provided files for examples.

---

## 🚀 How to Use

> **Requires:** Python **3.11.13** or higher.
> **Recommended:** Use a virtual environment (e.g., Anaconda or `python -m venv`).

### 1. ✅ Create & Activate Environment

```bash
# (Optional, but recommended)
conda create --prefix ./.venv python=3.11.13
conda activate ./.venv
```

or with venv:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 🏗️ Install Project 

Change directory to your project folder, then run:

```bash
pip install .
```

### 3. ⚙️ Configure Parameters

Edit `config/config.yaml` to set your project ID, file path, model, and generation parameters.

### 4. 🏃‍♂️ Run Inference

You can either:

* **Run via CLI entrypoint** (recommended):

  ```bash
  inference
  ```

  (Make sure you are in the project’s root directory.)

* **Or run the Jupyter notebook:**

  ```bash
  jupyter notebook jupyter/run_inference.ipynb
  ```

---

## 📝 Output

Results will be saved to:

* `misc/output/results.json` — successful outputs
* `misc/output/failed_requests.json` — failed files and error messages

---

## 🖼️ Input Types

* ✅ PDF files
* ✅ Image files (`.jpg`, `.png`)
* ⚠️ **Only supports structured output** generation using the provided schema and prompt.

---



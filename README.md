# 🎙️ VoiceChatLLM

**A proof-of-concept chat application powered by a language model (LLM) with voice-based interaction. Users can speak to the model and receive spoken responses.**



## 📌 Overview

VoiceChatLLM explores the fusion of natural language processing and voice interaction. It enables users to engage in spoken conversations with a language model, receiving both textual and spoken replies. The project is designed to be modular and extensible, with initial implementations provided via Jupyter Notebooks on Google Colab.



## 🧠 Features

- 🔊 Voice input and output for seamless interaction
- 🧾 Jupyter Notebook-based applications hosted on Google Colab
- 🐍 Python scripts for core logic and utilities
- 🖥️ Upcoming support for local desktop applications
- ⚙️ All configuration and usage instructions embedded directly in notebooks



## 🚀 Getting Started

### 1. Run on Google Colab

To launch the application:

- Open any of the provided `.ipynb` notebooks in Google Colab
- Follow the embedded instructions to configure and run the app
- Use your microphone to interact with the LLM

> 💡 No installation required — everything runs in the cloud!

### 2. Local Applications (Coming Soon)

We are actively developing standalone versions of VoiceChatLLM that will run locally on your machine. Stay tuned for updates!

### 🛠️ Local Setup Instructions (For testing purposes only)

To run VoiceChatLLM locally, follow these steps:

#### ✅ 1. Clone the Repository

```bash
git clone https://github.com/artbert/VoiceChatLLM.git
cd VoiceChatLLM
```


#### ✅ 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```



#### ✅ 3. Install Dependencies

```bash
pip install -r requirements.txt
```



#### ✅ 4. Run the Local Test Notebook

Launch the notebook to test microphone input, Text-to-Speech (TTS), and Speech-to-Text (STT):

```bash
jupyter notebook voice_interaction_test_app_local.ipynb
```



#### 🎤 Hardware Requirements

- A working **microphone**
- Speakers or headphones for audio output



#### ⚠️ Notes
- GPU is **not required** for basic voice interaction, but may be needed for advanced models like Bielik.
- The notebook is a work in progress, and features may be added in the future.



## 📂 Project Structure

```plaintext
VoiceChatLLM/
├── Voice_LLM_Chat_Colab.ipynb               # Colab notebook using an English-language model (no GPU required)
├── Voice_Chat_With_Bielik_Colab.ipynb       # Colab notebook using a Polish-language model (GPU required)
├── voice_interaction_test_app_local.ipynb   # Local notebook for testing TTS, STT, and microphone input/output
├── utils/                                   # Python modules supporting voice interaction and LLM logic
│   ├── voice_llm_chat_frontend.py           # Handles frontend logic and user interaction flow
│   ├── voice_llm_chat.py                    # Core backend logic for LLM communication and voice processing
│   └── ...                                  # Additional utility scripts
├── LICENSE                                  # Project license information
├── README.md                                # Main project documentation
└── requirements.txt                         # Python dependencies for local execution (if applicable)
```



## 🔗 Launch Notebooks on Google Colab

| Notebook | Language | GPU Required | Launch |
|----------|----------|--------------|--------|
| `Voice_LLM_Chat_Colab.ipynb` | English | ❌ No | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/artbert/VoiceChatLLM/blob/main/Voice_LLM_Chat_Colab.ipynb) |
| `Voice_Chat_With_Bielik_Colab.ipynb` | Polish | ✅ Yes | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/artbert/VoiceChatLLM/blob/main/Voice_Chat_With_Bielik_Colab.ipynb) |



## ⚙️ Requirements

- **Python**: 3.12+
- **Libraries**: Listed in `requirements.txt` (for local use)
- **Hardware**:
  - Google Colab: GPU optional (depending on notebook)
  - Local: Microphone required for voice interaction testing



## 📣 Contributing

Contributions are welcome! Feel free to fork the repo, submit issues, or open pull requests to improve functionality or add new features.



## 📄 License

This project is released under the [MIT License](LICENSE).



## 🙋‍♂️ Contact

For questions, suggestions, or collaboration inquiries, please open an issue or reach out via GitHub.



## ✨ Acknowledgments

Thanks to the open-source community and the developers of the language models and voice libraries that make this project possible.
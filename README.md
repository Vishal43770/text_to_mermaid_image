# Text to Mermaid Image Generator (Gemini Version)

This tool converts natural language descriptions of logical flows into professional Mermaid diagrams and renders them as high-quality PNG images using the Gemini API.

## Features

- **AI-Powered Parsing**: Uses Gemini to extract nodes, edges, types, and titles from your descriptions.
- **Professional Styling**: Automatically applies standard flowchart shapes (rectangles, diamonds, cylinders, etc.) and themes.
- **Automatic Rendering**: Generates a Mermaid script and downloads the rendered image via `mermaid.ink`.
- **Flexible API Key Management**: 
  - Automatically loads `GOOGLE_API_KEY` from a `.env` file.
  - If no key is found, it prompts you to enter it in the terminal.

## Prerequisites

- Python 3.x
- A Google Gemini API Key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Vishal43770/text_to_mermaid_image.git
   cd text_to_mermaid_image
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the generator:
   ```bash
   python3 main.py
   ```
2. If prompted, enter your `GOOGLE_API_KEY`.
3. Describe your flow (e.g., "A user logs in, checks their balance, and then either transfers money or logs out").
4. The tool will:
   - Generate the Mermaid code.
   - Save a PNG image in the `images/` directory.

## Environment Variables

You can create a `.env` file in the root directory to store your API key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

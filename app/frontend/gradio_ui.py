import gradio as gr
import requests
import re
import argparse

def get_urls(base_url: str):
    return {
        "detect": f"{base_url}/api/detection/detect",
        "mask": f"{base_url}/api/masking/mask"
    }

def ner_via_api(text: str, urls: dict):
    response = requests.post(urls["detect"], json={"text": text})
    if response.status_code == 200:
        return response.json()
    return {"text": text, "entities": []}

def mask_with_html_highlight(text: str, urls: dict):
    response = requests.post(urls["mask"], json={"text": text})
    if response.status_code == 200:
        data = response.json()
        masked_text = data.get("masked_text", text)
        
        # Color mapping
        color_map = {
            "EMAIL": "#ff6b6b",
            "STREET_ADDRESS": "#4ecdc4", 
            "PHONE_NUM": "#45b7d1",
            "ID_NUM": "#9b59b6",
            "NAME_STUDENT": "#f39c12",
            "URL_PERSONAL": "#e67e22",
            "USERNAME": "#8b4513"
        }
        
        # Replace masked tokens with colored HTML
        highlighted_text = masked_text
        for label, color in color_map.items():
            pattern = f"\\[{label}\\]"
            replacement = f'<span style="background-color: {color}; padding: 2px 4px; border-radius: 3px; color: white; font-weight: bold;">[{label}]</span>'
            highlighted_text = re.sub(pattern, replacement, highlighted_text)
        
        return highlighted_text
    else:
        return text

def gradio_launch(urls: dict):
    with gr.Blocks(title="PII Detector") as demo:
        gr.Markdown("# 🕵️ Education PII Detector")

        with gr.Tab("🔍 Detect PII"):
            with gr.Row():
                with gr.Column():
                    input_text = gr.Textbox(
                        label="Enter text",
                        placeholder="Type or paste text with PII...",
                        lines=10
                    )
                    submit_btn = gr.Button("🔍 Detect PII", variant="primary")
                with gr.Column():
                    output_box = gr.HighlightedText(label="Detection Results")
                    copy_detect_btn = gr.Button("📋 Copy")

            submit_btn.click(lambda t: ner_via_api(t, urls), inputs=input_text, outputs=output_box)
            copy_detect_btn.click(
                None, inputs=output_box, outputs=None,
                js="(x) => navigator.clipboard.writeText(JSON.stringify(x))"
            )

        with gr.Tab("🎨 Mask PII"):
            with gr.Row():
                with gr.Column():
                    mask_input = gr.Textbox(
                        label="Enter text",
                        placeholder="Type or paste text with PII...",
                        lines=10
                    )
                    mask_btn = gr.Button("🎨 Mask", variant="primary")
                with gr.Column():
                    gr.Markdown("### 🛡️ Masked Results")
                    mask_output = gr.HTML()
                    copy_mask_btn = gr.Button("📋 Copy", variant="secondary")

            mask_btn.click(lambda t: mask_with_html_highlight(t, urls), inputs=mask_input, outputs=mask_output)
            copy_mask_btn.click(
                None, inputs=mask_output, outputs=None,
                js="""
                (x) => {
                    const tmp = document.createElement('div');
                    tmp.innerHTML = x;
                    const textOnly = tmp.textContent || tmp.innerText;
                    navigator.clipboard.writeText(textOnly);
                }
                """
            )

    demo.launch()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--url', 
        type=str, 
        default="http://localhost:30000", 
        help="Base FastAPI URL"
    )
    args = parser.parse_args()
    urls = get_urls(args.url)
    gradio_launch(urls)

if __name__ == "__main__":
    main()
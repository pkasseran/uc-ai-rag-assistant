import json
import re
import sys
import os
import yaml
import shutil

class GroupDocumentForRAG:
    def __init__(self, input_json, output_json):
        # Always use ./outputs directory relative to this script
        output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        self.input_json = os.path.join(output_dir, os.path.basename(input_json))
        self.output_json = os.path.join(output_dir, os.path.basename(output_json))
        self.chunks = []
        self.current_title = None
        self.current_content = []
        self.current_source = None

    def remove_emojis(self, text):
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002700-\U000027BF"  # Dingbats
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r'', text)


    def validate_json(self, data):
        if not isinstance(data, list):
            print("Input JSON must be a list of dicts.")
            return False
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                print(f"Entry {i} is not a dict.")
                return False
            for key in ["source", "tag", "text"]:
                if key not in entry:
                    print(f"Entry {i} missing key: {key}")
                    return False
        return True

    def flush_group(self, source, title, content):
        if title and content:
            self.chunks.append({
                "source": source,
                "title": title,
                "content": "\n\n".join(content).strip(),
                "length": len("\n\n".join(content).strip())
            })

    def convert(self):
        with open(self.input_json, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        if not self.validate_json(raw_data):
            sys.exit(1)

        current_title = None
        current_content = []
        current_source = None

        for entry in raw_data:
            tag = entry.get("tag")
            text = self.remove_emojis(entry.get("text", "").strip())
            text = text.replace("¶", "")
            text = text.strip()
            source = entry.get("source", "")

            # If we see a new h1, flush the previous chunk (with previous source/title/content)
            if tag == "h1":
                self.flush_group(current_source, current_title, current_content)
                current_title = text.strip()
                current_content = [f"# {current_title}"]
                current_source = source
            elif tag == "h2":
                current_content.append(f"## {text}")
            elif tag == "h3":
                current_content.append(f"### {text}")
            elif tag == "h4":
                current_content.append(f"#### {text}")
            elif tag in ["p", "pre", "code", "ul", "li"]:
                current_content.append(text)
            # If the source changes (but not a new h1), flush as well
            elif source and source != current_source and current_title:
                self.flush_group(current_source, current_title, current_content)
                current_title = None
                current_content = []
                current_source = source

        # Flush the last group if any content remains
        self.flush_group(current_source, current_title, current_content)

        with open(self.output_json, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        print(f"✅ Created {len(self.chunks)} RAG-ready groups at: {self.output_json}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_to_groups.py <config_yaml>")
        sys.exit(1)
    config_yaml = sys.argv[1]
    if not os.path.exists(config_yaml):
        print(f"Config file not found: {config_yaml}")
        sys.exit(1)
    with open(config_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    input_json = config.get("output_raw_file")
    output_json = config.get("output_rag_grouping_file")
    if not input_json or not output_json:
        print("YAML config must contain 'output_raw_file' and 'output_rag_grouping_file' keys.")
        sys.exit(1)
    converter = GroupDocumentForRAG(input_json, output_json)
    converter.convert()

    # Copy output_json to ROOT_DIR/../../documents
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, "../../"))
    documents_dir = os.path.join(root_dir, "documents")
    copy_from_path = os.path.abspath(os.path.join(script_dir, "outputs", os.path.basename(output_json)))
    os.makedirs(documents_dir, exist_ok=True)
    dest_path = os.path.join(documents_dir, os.path.basename(output_json))
    shutil.copy2(copy_from_path, dest_path)
    print(f"✅ Copied {copy_from_path} to {dest_path}")

if __name__ == "__main__":
    main()
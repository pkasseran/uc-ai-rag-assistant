import os
import yaml

class ConfigLoader:
    def __init__(self, root_dir: str):
        self.config_dir = os.path.join(root_dir, "config")
    
    def get_prompt_config(self):
        yaml_path = os.path.join(self.config_dir, "prompt_config.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def get_config(self):
        yaml_path = os.path.join(self.config_dir, "config.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def build_rag_prompt(self, prompt_config_val, reasoning_strategy=None):
        style_tone = "\n".join(f"- {item}" for item in prompt_config_val.get("style_or_tone", []))
        constraints = "\n".join(f"- {item}" for item in prompt_config_val.get("output_constraints", []))
        output_format = "\n".join(f"- {item}" for item in prompt_config_val.get("output_format", []))

        prompt = f"""{prompt_config_val['role'].strip()}

Follow these style and tone guidelines in your response:
{style_tone}

Ensure your response follows these constraints:
{constraints}

Ensure your response adheres to the following output format:
{output_format}

"""
        if reasoning_strategy:
            prompt += f"\nUse the following reasoning strategy:\n{reasoning_strategy}\n"

        prompt += """
<context>
{context}
</context>

Question: {question}
Answer:
"""
        return prompt
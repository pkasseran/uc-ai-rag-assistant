import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
import os
from typing import List, Dict, Any
import logging
from urllib.parse import urljoin  

class WebDocumentScraper:
    """
    A web scraper class for extracting structured content from documentation websites.
    Supports configuration via YAML files for URLs and output settings.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the scraper with optional configuration file.
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config = {}
        self.setup_logging()
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to YAML configuration file
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to load config file {config_file}: {e}")
            raise

    def resolve_url_if_needed(self, href: str, source_url: str) -> str:
        """
        Resolve relative URLs to absolute URLs based on configuration.
        
        Args:
            href: The href attribute value
            source_url: The source URL being scraped
            
        Returns:
            Resolved URL or original href
        """
        if not href:
            return href
            
        # Get URL processing configuration
        url_config = self.config.get('url_processing', {})
        resolve_relative = url_config.get('resolve_relative_urls', True)
        log_changes = url_config.get('log_url_changes', False)
        
        if resolve_relative:
            original_href = href
            resolved_href = urljoin(source_url, href)
            
            if log_changes and original_href != resolved_href:
                self.logger.debug(f"Resolved URL: {original_href} -> {resolved_href}")
            
            return resolved_href
        
        return href
    
    def scrape_urls(self, 
                   urls: List[str] = None, 
                   output_file: str = None,
                   tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape content from a list of URLs.
        
        Args:
            urls: List of URLs to scrape (overrides config)
            output_file: Output JSON file name (overrides config)
            tags: HTML tags to extract (overrides config)
            
        Returns:
            List of extracted content dictionaries
        """
        # Use parameters or fall back to config
        urls = urls or self.config.get('urls', [])
        output_file = output_file or self.config.get('output_raw_file', 'scraped_docs.json')
        tags = tags or self.config.get('tags', ["h1", "h2", "h3", "h4", "p", "pre", "li", "ul"])
        
        if not urls:
            raise ValueError("No URLs provided. Either pass urls parameter or configure in YAML file.")
        
        data = []
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs")
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Scraping URL {i}/{len(urls)}: {url}")
            
            try:
                content = self.scrape_single_url(url, tags)
                data.extend(content)
                self.logger.info(f"Extracted {len(content)} elements from {url}")
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                continue
        
        # Save to file
        self.save_to_json(data, output_file)
        
        self.logger.info(f"Scraping completed. Total elements extracted: {len(data)}")
        return data
    
    def scrape_single_url(self, url: str, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape content from a single URL.
        
        Args:
            url: URL to scrape
            tags: HTML tags to extract
            
        Returns:
            List of content dictionaries for this URL
        """
        # Fetch the page
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        content = []
        
        # Extract content from specified tags
        for section in soup.find_all(tags):
            extracted_data = self.process_html_element(section, url)
            if extracted_data:
                content.append(extracted_data)
        
        return content
    
    def process_html_element(self, element, source_url: str) -> Dict[str, Any]:
        tag = element.name
        text = ""

        # Handle code blocks
        if tag == "pre":
            code_block = element.find("code")
            if code_block:
                text = code_block.get_text()
                text = f"```\n{text.strip()}\n```"
                tag = "code"
            else:
                text = element.get_text().strip()

        # Paragraphs
        elif tag == "p":
            # If the <p> contains <a> tags, format each as markdown link and preserve context
            links = element.find_all("a")
            if links:
                parts = []
                last_idx = 0
                text_str = str(element)
                for a in links:
                    # Get the text before the link
                    link_html = str(a)
                    link_text = a.get_text(strip=True)
                    href = a.get("href", "").strip()
                    
                    # Resolve URL using configuration
                    if href:
                        href = self.resolve_url_if_needed(href, source_url)
                        print(f"Resolved link: {link_text} -> {href}")
                    
                    # Find where this link appears in the HTML
                    idx = text_str.find(link_html, last_idx)
                    if idx > last_idx:
                        # Add any text before the link
                        before = BeautifulSoup(text_str[last_idx:idx], "html.parser").get_text(separator=" ", strip=True)
                        if before:
                            parts.append(before)
                    # Add the markdown link
                    if href:
                        parts.append(f"[{link_text}]({href})")
                    else:
                        parts.append(link_text)
                    last_idx = idx + len(link_html)
                # Add any text after the last link
                after = BeautifulSoup(text_str[last_idx:], "html.parser").get_text(separator=" ", strip=True)
                if after:
                    parts.append(after)
                text = " ".join(parts)
            else:
                text = element.get_text().strip()

        # Lists: ul, ol, li
        elif tag in ["ul", "ol"]:
            # For each <li> in the list, process as a markdown list item
            items = []
            for li in element.find_all("li", recursive=False):
                # If the <li> contains <a>, format as markdown link
                links = li.find_all("a")
                if links:
                    for a in links:
                        link_text = a.get_text(strip=True)
                        href = a.get("href", "").strip()
                        if href:
                            # Resolve URL using configuration
                            href = self.resolve_url_if_needed(href, source_url)
                            items.append(f"- [{link_text}]({href})")
                        else:
                            items.append(f"- {link_text}")
                else:
                    li_text = li.get_text(separator=" ", strip=True)
                    items.append(f"- {li_text}")
            text = "\n".join(items)

        elif tag == "li":
            # If the <li> contains <a>, format as markdown link
            links = element.find_all("a")
            if links:
                items = []
                for a in links:
                    link_text = a.get_text(strip=True)
                    href = a.get("href", "").strip()
                    if href:
                        # Resolve URL using configuration
                        href = self.resolve_url_if_needed(href, source_url)
                        items.append(f"- [{link_text}]({href})")
                    else:
                        items.append(f"- {link_text}")
                text = "\n".join(items)
            else:
                text = "- " + element.get_text(separator=" ", strip=True)

        # Headings
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = element.get_text().strip()

        # For <a> tags directly
        elif tag == "a":
            link_text = element.get_text(strip=True)
            href = element.get("href", "").strip()
            if href:
                # Resolve URL using configuration
                href = self.resolve_url_if_needed(href, source_url)
                text = f"[{link_text}]({href})"
            else:
                text = link_text

        else:
            text = element.get_text(separator=" ", strip=True)

        if text:
            return {
                "source": source_url,
                "tag": tag,
                "text": text,
                "length": len(text)
            }
        return None

    def save_to_json(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save extracted data to JSON file.
        
        Args:
            data: List of content dictionaries
            output_file: Output file path
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_file_fullpath = os.path.join(output_dir, os.path.basename(output_file))
            with open(output_file_fullpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(data)} items to {output_file_fullpath}")

        except Exception as e:
            self.logger.error(f"Failed to save data to {output_file_fullpath}: {e}")
            raise

def main():
    """
    Main function for command-line usage.
    Usage: python web_scraper.py config.yaml
    """
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python web_scraper.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        scraper = WebDocumentScraper(config_file)
        scraper.scrape_urls()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()